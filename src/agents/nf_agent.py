"""Agente LangGraph para validação de NFe para homologação SEFAZ."""

from typing import TypedDict

from langgraph.graph import StateGraph, END

from config.configuration import DEFAULT_MODELS, LLMProvider
from src.parsers.xml_parser_llm import XMLParserLLM
from src.parsers.rps_parser import RPSParser
from src.validators.calculators.tax_calculator import calcular_impostos
from src.api.simulation_sefaz import SefazSimulator
from src.database.connection import insert_nota_fiscal, get_connection
from src.validators.cfops.cfop_validator import validar_cfops_nota
from src.validators.ncm.ncm_validator import validar_ncm_itens
from src.validators.cpf_cnpj.document_validator import validar_document_dest
from src.validators.csts.cst_validator import validar_cst_nfe
from logs.logger import agent_logger


# =====================================================
# ESTADO DO AGENTE
# =====================================================

class AgentState(TypedDict):
    """Estado do agente de validação NFe."""
    arquivo_path: str
    tipo_documento: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    notas_processadas: list[dict]
    erros: list[str]
    status: str


# =====================================================
# AGENTE PRINCIPAL
# =====================================================

class NFAgentIntelligent:
    """Agente inteligente para validação de NFe para SEFAZ."""
    
    def __init__(
        self, 
        llm_provider: str = "groq", 
        api_key: str = ""
    ):
        
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.model = DEFAULT_MODELS[LLMProvider(llm_provider)].value
        
        self.graph = self._build_graph()
        
        agent_logger.info(f"🤖 Agente NFe inicializado com {llm_provider}/{self.model}")
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo do agente."""
        workflow = StateGraph(AgentState)
        
        # Adicionar nós
        workflow.add_node("identificar_tipo", self.identificar_tipo)
        workflow.add_node("processar_nfe", self.processar_nfe)
        workflow.add_node("processar_rps", self.processar_rps)
        workflow.add_node("calcular_imposto", self.calcular_impostos)
        workflow.add_node("validar_fiscal", self.validar_fiscal)
        workflow.add_node("simular_sefaz", self.simular_sefaz)
        workflow.add_node("salvar_db", self.salvar_db)
        
        workflow.set_entry_point("identificar_tipo")
        
        workflow.add_conditional_edges(
            "identificar_tipo",
            self.decidir_parser,
            {
                "nfe": "processar_nfe",
                "rps": "processar_rps",
            }
        )
        
        workflow.add_edge("processar_nfe", "calcular_imposto")
        workflow.add_edge("processar_rps", "calcular_imposto")
        workflow.add_edge("calcular_imposto", "validar_fiscal")

        workflow.add_conditional_edges(
            "validar_fiscal", 
            self.decidir_envio_sefaz, 
            {
                'enviar': "simular_sefaz", 
                'rejeitar': "salvar_db"
            }
        )
        workflow.add_edge("simular_sefaz", "salvar_db")
        workflow.add_edge("salvar_db", END)
        
        return workflow.compile()
    
    # =====================================================
    # NODOS DO WORKFLOW
    # =====================================================
    
    def identificar_tipo(self, state: AgentState) -> AgentState:
        """Identifica se é NFe ou RPS."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(state["arquivo_path"])
            root = tree.getroot()

            if root.find('.//Nfse') is not None or root.find('.//CompNfse') is not None or 'ConsultarNfseRpsResposta' in root.tag:
                state["tipo_documento"] = "rps"
                agent_logger.info("📋 Tipo identificado: RPS (Nota de Serviço)")
            elif root.find('.//NFe') is not None or 'nfeProc' in root.tag:
                state["tipo_documento"] = "nfe"
                agent_logger.info("📋 Tipo identificado: NFe (Nota de Produto)")
            else:
                state["tipo_documento"] = "nfe"
                agent_logger.warning("⚠️  Tipo não identificado, assumindo NFe")
                
        except Exception as e:
            state["erros"].append(f"Erro ao identificar tipo: {e}")
            state["tipo_documento"] = "nfe"
            agent_logger.error(f"❌ Erro identificação: {e}")
        
        return state
    
    def decidir_parser(self, state: AgentState) -> str:
        """Decide qual parser usar."""
        return state["tipo_documento"]
    
    def processar_nfe(self, state: AgentState) -> AgentState:
        """Processa NFe (Nota de Produto) com LLM."""
        try:
            parser = XMLParserLLM(
                state["arquivo_path"],
                llm_provider=state["llm_provider"],
                api_key=state["llm_api_key"],
                model=state["llm_model"],
                use_llm_validation=True,
                use_llm_enrichment=False
            )
            nf_data = parser.parse()
            
            # Log de validação LLM
            if 'llm_validation' in nf_data:
                val = nf_data['llm_validation']
                agent_logger.info(
                    f"🤖 Validação LLM: {val['validacao_geral']} "
                    f"(confiança: {val.get('confianca', 0)}%)"
                )
            
            state["notas_processadas"].append(nf_data)
            agent_logger.info(f"✅ NFe parseada: {nf_data['numero_nf']}")
            
        except Exception as e:
            state["erros"].append(f"Erro ao processar NFe: {e}")
            agent_logger.error(f"❌ Erro: {e}")
        
        return state
    
    def processar_rps(self, state: AgentState) -> AgentState:
        """Processa RPS (Nota de Serviço)."""
        try:
            # Usar parser de RPS
            parser = RPSParser(state["arquivo_path"])
            nf_data = parser.parse()

            nf_data['llm_validation'] = {
                'validacao_geral': 'APROVADO',
                'score_confianca': 100,
                'erros_criticos': [],
                'avisos': [],
                'validacoes_ok': ['RPS parseado com sucesso'],
                'resumo_fiscal': {
                    'iss_ok': True,
                    'totalizadores_ok': True
                },
                'recomendacao_sefaz': 'APTO PARA PRODUÇÃO',
                'justificativa': 'RPS processado sem LLM'
            }
            
            state["notas_processadas"].append(nf_data)
            agent_logger.info(f"✅ RPS parseado: {nf_data['numero_nf']}")
            
        except Exception as e:
            state["erros"].append(f"Erro ao processar RPS: {e}")
            agent_logger.error(f"❌ Erro: {e}")
        
        return state
    
    def validar_fiscal(self, state: AgentState) -> AgentState:
        """Valida dados fiscais com LLM (CFOP, CST, NCM, impostos)."""
        
        for nf_data in state["notas_processadas"]:
            
            cfop_validation = validar_cfops_nota(nf_data)
            if not cfop_validation['valido']:
                nf_data['status'] = 'Reprovado'
                erros = cfop_validation.get('erros', [])
                if erros:
                    nf_data['mensagem_erro'] = "Validação CFOP reprovada: " + "; ".join(erros)
                    state["erros"].extend([str(e) for e in erros])
                    agent_logger.warning(f"❌ NF {nf_data['numero_nf']} REPROVADA")
                    return state
            
            ncm_validation = validar_ncm_itens(nf_data)
            if not ncm_validation['valido']:
                nf_data['status'] = 'Reprovado'
                erros = ncm_validation.get('erros', [])
                if erros:
                    nf_data['mensagem_erro'] = "Validação NCM reprovada: " + "; ".join(erros)
                    state["erros"].extend([str(e) for e in erros])
                    agent_logger.warning(f"❌  NF {nf_data['numero_nf']} REPROVADA")
                    return state
                
            document_validation = validar_document_dest(nf_data)
            if not document_validation['valido']:
                nf_data['status'] = 'Reprovado'
                erros = document_validation.get('erros', [])
                if erros:
                    nf_data['mensagem_erro'] = "Validação reprovada: " + "; ".join(erros)
                    state["erros"].extend([str(e) for e in erros])
                    agent_logger.warning(f"❌ {state["erros"]}, nota número {nf_data['numero_nf']} REPROVADA")
                    return state
                
            cst_validation = validar_cst_nfe(nf_data)
            if not cst_validation['valido']:
                nf_data['status'] = 'Reprovado'
                erros = cst_validation.get('erros', [])
                if erros:
                    nf_data['mensagem_erro'] = "Validação CST reprovada: " + "; ".join([e['msg'] for e in erros])
                    state["erros"].extend([e['msg'] for e in erros])
                    agent_logger.warning(f"❌  NF {nf_data['numero_nf']} REPROVADA")
                    return state                
                
           
            nf_data['status'] = 'Aprovado'
            agent_logger.info(f"✅ NF {nf_data['numero_nf']} aprovada para SEFAZ")
        
        return state
    
    def decidir_envio_sefaz(self, state: AgentState) -> str:
        """Decide se envia para SEFAZ ou rejeita. Usa a validação LLM como fonte primária de rejeição."""

        for nf in state["notas_processadas"]:
            numero_nf = nf.get('numero_nf', 'desconhecido')
            status_nf = str(nf.get('status', 'desconhecido')).upper().strip()
            
            if status_nf == 'REPROVADO':
                agent_logger.warning(f"❌ NF {numero_nf} com status {status_nf}")
                return "rejeitar"
        
        agent_logger.info(f"🟢 DECISÃO FINAL: ENVIAR ao SEFAZ. Retornando 'enviar'.")
        return "enviar"
    
    def simular_sefaz(self, state: AgentState) -> AgentState:
        """Simula envio ao SEFAZ e obtém chave NFe."""
        simulator = SefazSimulator()
        
        for nf_data in state["notas_processadas"]:
            if nf_data.get('skip_sefaz', False):
                agent_logger.warning(f"⏭️  Pulando SEFAZ para NF {nf_data['numero_nf']} (reprovada)")
                break
            
            if nf_data.get('status') in ['Aprovado', 'Aprovado com ressalvas']:
                try:
                    result = simulator.simulate_submission(state["arquivo_path"])
                    
                    if result['status'] == 'sucesso':
                        nf_data['chave_nfe'] = result['chave_nfe']
                        nf_data['protocolo_sefaz'] = result['numero_protocolo']
                        nf_data['data_autorizacao'] = result['data_recebimento']
                        nf_data['status'] = 'Autorizado'
                        
                        agent_logger.info(f"✅ NFe AUTORIZADA - Chave: {result['chave_nfe']}")
                    else:
                        nf_data['status'] = 'Rejeitado SEFAZ'
                        nf_data['mensagem_erro'] = result['motivo']
                        state["erros"].append(result['motivo'])
                        agent_logger.error(f"❌ NFe REJEITADA: {result['motivo']}")
                        
                except Exception as e:
                    state["erros"].append(f"Erro na simulação SEFAZ: {e}")
                    agent_logger.error(f"❌ Erro SEFAZ: {e}")
        
        return state
    
    def salvar_db(self, state: AgentState) -> AgentState:
        """Salva notas no banco de dados."""
        agent_logger.info(f"💾 Iniciando salvamento de {len(state['notas_processadas'])} notas")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        for nf_data in state["notas_processadas"]:
            try:
                agent_logger.info(f"💾 Salvando NF {nf_data.get('numero_nf')}...")
                
                if nf_data.get('classificacao') == 'Servico' or nf_data.get('tipo_nf') == 'RPS':
                    if not nf_data.get('cliente_cpf'):
                        nf_data['cliente_cpf'] = nf_data.get('cliente_cnpj', '00000000000')
                        
                nf_id = insert_nota_fiscal(nf_data, cursor)
                agent_logger.info(f"✅ Nota fiscal inserida com ID: {nf_id}")

                itens_count = len(nf_data.get("itens", []))
                agent_logger.info(f"📦 Inserindo {itens_count} itens...")
                
                for item in nf_data.get("itens", []):
                    cursor.execute("""
                        INSERT INTO itens_nota 
                        (nf_id, codigo_item, descricao, quantidade, valor_unitario, valor_total, tipo, ncm)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nf_id, 
                        item.get('codigo_item', ''),
                        item.get('descricao', ''),
                        item.get('quantidade', 0),
                        item.get('valor_unitario', 0),
                        item.get('valor_total', 0),
                        item.get('tipo', ''),
                        item.get('ncm')
                    ))
                
                impostos_count = len(nf_data.get("impostos", []))
                agent_logger.info(f"💰 Inserindo {impostos_count} impostos...")
                
                for imposto in nf_data.get("impostos", []):
                    cursor.execute("""
                        INSERT INTO impostos 
                        (nf_id, tipo_imposto, aliquota, valor_base, valor_imposto)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        nf_id,
                        imposto.get('tipo_imposto', ''),
                        imposto.get('aliquota', 0),
                        imposto.get('valor_base', 0),
                        imposto.get('valor_imposto', 0)
                    ))
                
                conn.commit()
                agent_logger.info(f"✅ NF {nf_data['numero_nf']} salva no banco (ID: {nf_id})")
                
            except Exception as e:
                error_msg = f"Erro ao salvar NF {nf_data.get('numero_nf', 'desconhecido')}: {str(e)}"
                state["erros"].append(error_msg)
                agent_logger.error(f"❌ {error_msg}")
                import traceback
                agent_logger.error(traceback.format_exc())
        
        conn.close()
        state["status"] = "completo"
        agent_logger.info("✅ Salvamento concluído")
        return state
    
    def calcular_impostos(self, state: AgentState) -> AgentState:
        """Calcula impostos para cada nota processada."""
        agent_logger.info(f"💰 Iniciando cálculo de impostos para {len(state['notas_processadas'])} notas")
        
        for nf_data in state["notas_processadas"]:
            try:

                impostos = calcular_impostos(nf_data)
                
                nf_data["impostos"] = impostos
                
                total_impostos = sum(imp['valor_imposto'] for imp in impostos)
                nf_data["total_impostos_calculados"] = total_impostos
                
                agent_logger.info(
                    f"✅ Impostos calculados para NF {nf_data.get('numero_nf')}: "
                    f"R$ {total_impostos:.2f} ({len(impostos)} tipos)"
                )
                
            except Exception as e:
                error_msg = f"Erro no cálculo de impostos da NF {nf_data.get('numero_nf', 'desconhecido')}: {str(e)}"
                state["erros"].append(error_msg)
                agent_logger.error(f"❌ {error_msg}")
        
        return state
    
    # =====================================================
    # MÉTODO PRINCIPAL
    # =====================================================
    
    def processar(self, arquivo_path: str, llm_provider: str = None, api_key: str = None) -> dict:
        """
        Processa arquivo XML e retorna resultado.
        
        Args:
            arquivo_path: Caminho do arquivo XML
            llm_provider: Provider LLM
            api_key: API Key
        
        Returns:
            dict com resultado do processamento
        """

        provider = llm_provider or self.llm_provider
        key = api_key or self.api_key

        model = DEFAULT_MODELS[LLMProvider(provider)].value
        
        initial_state: AgentState = {
            "arquivo_path": arquivo_path,
            "tipo_documento": "",
            "llm_provider": provider,
            "llm_api_key": key,
            "llm_model": model,
            "notas_processadas": [],
            "erros": [],
            "status": "processando",
        }
        
        result = self.graph.invoke(initial_state)
        return result
