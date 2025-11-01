"""Parser XML melhorado com validação semântica via LLM."""

from pathlib import Path
from typing import Optional
import json

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from src.parsers.xml_parser import XMLParser
from logs.logger import parser_logger
from src.prompts.xml_extractor_prompt import VALIDATION_PROMPT, ENRICHMENT_PROMPT


class XMLParserLLM:
    """Parser XML melhorado com validação semântica LLM."""
    
    def __init__(
        self,
        file_path: str | Path,
        llm_provider: str = "groq",
        api_key: str = "",
        model: str = "mixtral-8x7b-32768",
        use_llm_validation: bool = True,
        use_llm_enrichment: bool = True
    ):
        """Inicializa parser."""
        self.file_path = Path(file_path)
        self.base_parser = XMLParser(file_path)
        self.llm = None
        self.use_llm_validation = use_llm_validation and api_key
        self.use_llm_enrichment = use_llm_enrichment and api_key
        
        if api_key:
            self.llm = self._setup_llm(llm_provider, api_key, model)
            parser_logger.info(f"🤖 XML Parser LLM ativado com {llm_provider}/{model}")
        else:
            parser_logger.info("📄 XML Parser padrão (sem LLM)")
    
    def _setup_llm(self, provider: str, api_key: str, model: str):
        """Configura LLM."""
        provider = provider.lower()
        
        if provider == "openai":
            return ChatOpenAI(api_key=api_key, model=model, temperature=0.1)
        elif provider == "groq":
            return ChatGroq(api_key=api_key, model=model, temperature=0.1)
        elif provider == "claude":
            return ChatAnthropic(api_key=api_key, model=model, temperature=0.1)
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(api_key=api_key, model=model, temperature=0.1)
        else:
            raise ValueError(f"Provider não suportado: {provider}")
    
    def parse(self) -> dict:
        """Faz parsing completo com validações LLM."""
        try:
            nf_data = self.base_parser.parse()
            parser_logger.info(f"✅ XML parseado: NF {nf_data['numero_nf']}")

            if self.use_llm_validation and self.llm:
                validation_result = self._validate_with_llm(nf_data)
                nf_data['llm_validation'] = validation_result
                
                if validation_result['validacao_geral'] == 'Reprovado':
                    parser_logger.warning(f"⚠️  Validação LLM: REPROVADO")
                    nf_data['status'] = 'Erro'
                    nf_data['mensagem_erro'] = "; ".join(validation_result['problemas_criticos'])

            if self.use_llm_enrichment and self.llm:
                enrichment_result = self._enrich_with_llm(nf_data)
                nf_data['llm_enrichment'] = enrichment_result
                
                if enrichment_result.get('natop_sugerido') and not nf_data.get('natop'):
                    nf_data['natop'] = enrichment_result['natop_sugerido']
                    parser_logger.info(f"💡 NATOP enriquecido: {enrichment_result['natop_sugerido']}")
            
            return nf_data
            
        except Exception as e:
            parser_logger.error(f"❌ Erro ao parsear XML com LLM: {e}")
            raise
    
    def _validate_with_llm(self, nf_data: dict) -> dict:
        """Valida dados com LLM."""
        try:
            # Preparar resumo dos itens
            itens_resumo = []
            for item in nf_data.get('itens', [])[:5]:
                itens_resumo.append({
                    'descricao': item.get('descricao', ''),
                    'tipo': item.get('tipo', ''),
                    'ncm': item.get('ncm', 'N/A'),
                    'valor': item.get('valor_total', 0)
                })
            
            prompt = VALIDATION_PROMPT.format(
                cfop=nf_data.get('cfop', ''),
                natop=nf_data.get('natop', ''),
                itens_resumo=json.dumps(itens_resumo, ensure_ascii=False),
                valor_total=nf_data.get('valor_total', 0),
                fornecedor_cnpj=nf_data.get('fornecedor_cnpj', ''),
                cliente_cnpj=nf_data.get('cliente_cnpj', ''),
                cliente_cpf=nf_data.get('cliente_cpf', '')
            )

            response = self.llm.invoke(prompt)
            response_text = response.content

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            validation_result = json.loads(response_text.strip())
            
            parser_logger.info(f"✅ Validação LLM: {validation_result['validacao_geral']} "
                             f"(confiança: {validation_result.get('confianca', 0)}%)")
            
            return validation_result
            
        except Exception as e:
            parser_logger.error(f"❌ Erro na validação LLM: {e}")
            return {
                'validacao_geral': 'ERRO',
                'problemas_criticos': [f'Erro ao validar com LLM: {str(e)}'],
                'avisos': [],
                'sugestoes_correcao': [],
                'confianca': 0,
                'justificativa': 'Falha na validação'
            }
    
    def _enrich_with_llm(self, nf_data: dict) -> dict:
        """Enriquece dados com LLM."""
        try:
            # Preparar itens para enriquecimento
            itens_para_enriquecer = []
            for item in nf_data.get('itens', [])[:5]:
                if not item.get('ncm'):  # Apenas itens sem NCM
                    itens_para_enriquecer.append({
                        'codigo_item': item.get('codigo_item', ''),
                        'descricao': item.get('descricao', '')
                    })

            prompt = ENRICHMENT_PROMPT.format(
                cfop=nf_data.get('cfop', ''),
                natop=nf_data.get('natop', ''),
                classificacao=nf_data.get('classificacao', ''),
                itens=json.dumps(itens_para_enriquecer, ensure_ascii=False)
            )

            response = self.llm.invoke(prompt)
            response_text = response.content
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            enrichment_result = json.loads(response_text.strip())
            
            parser_logger.info(f"💡 Dados enriquecidos com LLM")
            
            return enrichment_result
            
        except Exception as e:
            parser_logger.error(f"❌ Erro no enriquecimento LLM: {e}")
            return {
                'natop_sugerido': '',
                'classificacao_corrigida': '',
                'regime_tributario': '',
                'itens_enriquecidos': [],
                'insights': []
            }


def parse_xml_with_llm(
    file_path: str | Path,
    llm_provider: str = "groq",
    api_key: str = "",
    model: str = "mixtral-8x7b-32768",
    use_validation: bool = True,
    use_enrichment: bool = True
) -> dict:
    """Função auxiliar para parsear XML com LLM."""
    parser = XMLParserLLM(
        file_path, 
        llm_provider, 
        api_key, 
        model,
        use_validation,
        use_enrichment
    )
    return parser.parse()
