"""Parser para arquivos XML de NFe."""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import xmltodict

from src.constants import DocumentType, ClassificationType
from logs.logger import parser_logger


class XMLParser:
    """Parser para NFe XML."""
    
    def __init__(self, file_path: str | Path):
        """Inicializa parser."""
        self.file_path = Path(file_path)
        self.data = None
        
    def parse(self) -> dict:
        """Faz parsing do arquivo XML."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = xmltodict.parse(f.read())
            
            parser_logger.info(f"✅ Arquivo XML lido: {self.file_path.name}")
            return self._extract_data()
            
        except Exception as e:
            parser_logger.error(f"❌ Erro ao ler XML: {e}")
            raise
    
    def _extract_data(self) -> dict:
        """Extrai dados da NFe."""
        try:
            # Navegar na estrutura XML da NFe
            nfe_proc = self.data.get('nfeProc', {}) # Novo nó raiz
            nfe = nfe_proc.get('NFe', {})
            inf_nfe = nfe.get('infNFe', {})
            
            # 🌟 NOVO: Extrair dados do Protocolo
            prot_nfe = nfe_proc.get('protNFe', {})
            inf_prot = prot_nfe.get('infProt', {})
            
            # Identificação, Emitente, etc. (seu código existente)
            ide = inf_nfe.get('ide', {})
            emit = inf_nfe.get('emit', {})
            dest = inf_nfe.get('dest', {})
            total = inf_nfe.get('total', {}).get('ICMSTot', {})
            
            # Itens
            det = inf_nfe.get('det', [])
            if not isinstance(det, list):
                det = [det]
                
            main_cfop = ''
            find_cfops = set()
            if det:
                for item in det:
                    cfop_item = item.get('prod', {}).get('CFOP', '')
                    if cfop_item:
                        find_cfops.add(cfop_item)
                        if not main_cfop:
                            main_cfop = cfop_item
            
            if not main_cfop and find_cfops:
                main_cfop = list(find_cfops)[0]

            # Montar dicionário (Adicionar campos do Protocolo)
            classificacao = self._determinar_classificacao(det)
            
            nf_data = {
                'numero_nf': ide.get('nNF', ''),
                'serie': ide.get('serie', '1'),
                'numero_nf': ide.get('nNF', ''),
                'serie': ide.get('serie', '1'),
                'tipo_nf': DocumentType.NFE.value,
                'data_emissao': self._parse_datetime(ide.get('dhEmi', '')),
                'classificacao': classificacao.value,
                'cfop': main_cfop,
                'natop': ide.get('natOp', ''),
                'sct': 'N',  # Padrão
                'crt': emit.get('CRT', ''),
                'valor_total': float(total.get('vNF', 0)),
                'fornecedor_cnpj': emit.get('CNPJ', ''),
                'cliente_cnpj': dest.get('CNPJ', ''),
                'cliente_cpf': dest.get('CPF', ''),
                'itens': self._extract_itens(det),
                'impostos': self._extract_impostos(total, inf_nfe),
                'status': inf_prot.get('cStat', '999'),
                'impostos': self._extract_impostos(total, inf_nfe)
            }
            
            # Ajuste: A chave de acesso também pode ser obtida do infNFe
            #if not nf_data['chave_nfe']:
                # Pega a chave da tag 'chNFe' que vem no protNFe
            #    nf_data['chave_nfe'] = prot_nfe.get('chNFe', '') 

            # Correção no Status para o Banco
            # Se for Autorizado (100), define como 'Autorizado' no BD
            #if nf_data['status'] == '100':
            #    nf_data['status'] = 'Autorizado'
            #else:
            #    nf_data['status'] = 'Rejeitado' # Ou outro tratamento para códigos não 100
                
            parser_logger.info(f"✅ Dados extraídos da NF {nf_data['numero_nf']} (Status SEFAZ: {nf_data['status']})")
            return nf_data

        except Exception as e:
            parser_logger.error(f"❌ Erro ao extrair dados: {e}")
            raise
    
    def _determinar_classificacao(self, itens: list) -> ClassificationType:
        """Determina se é produto ou serviço."""
        has_produto = False
        has_servico = False
        
        for item in itens:
            prod = item.get('prod', {})
            # Se tem NCM, é produto
            if prod.get('NCM'):
                has_produto = True
            # Se não tem NCM, é serviço
            else:
                has_servico = True
        
        if has_produto and has_servico:
            return ClassificationType.AMBOS
        elif has_servico:
            return ClassificationType.SERVICO
        else:
            return ClassificationType.PRODUTO
    
    def _extract_itens(self, det: list) -> list[dict]:
        """Extrai itens da nota, incluindo CFOP, NCM e os códigos de imposto (CST/CSOSN) de forma robusta."""
        itens = []
        
        # Garantir que det seja uma lista se a NF só tiver um item
        if not isinstance(det, list):
            det = [det]

        for item in det:
            prod = item.get('prod', {})
            imposto = item.get('imposto', {})
            
            # --- Lógica de Extração Robusta do ICMS (CST/CSOSN, etc.) ---
            icms_data = imposto.get('ICMS', {})
            icms_detalhe = {}
            cst_csosn_valor = ''
            
            if icms_data:
                for key, value in icms_data.items():
                    if isinstance(value, dict) and key not in ['vICMSDeson', 'infAdProd']:
                        # 1. Corrigido: icms_detalhe armazena o DICIONÁRIO da tag de imposto (Ex: ICMSSN102)
                        icms_detalhe = value
                        # 2. Armazena o valor do CST/CSOSN separadamente
                        cst_csosn_valor = value.get('CST', value.get('CSOSN', '')) 
                        break

            # --- Lógica de Extração Robusta de IPI ---
            ipi_data = imposto.get('IPI', {})
            ipi_detalhe = {}
            cst_ipi = ''
            if ipi_data:
                for key, value in ipi_data.items():
                    if isinstance(value, dict):
                        ipi_detalhe = value
                        cst_ipi = value.get('CST', '') 
                        break
                        
            # --- Lógica de Extração Robusta de PIS ---
            pis_data = imposto.get('PIS', {})
            pis_detalhe = {}
            cst_pis = ''
            if pis_data:
                for key, value in pis_data.items():
                    if isinstance(value, dict):
                        pis_detalhe = value
                        cst_pis = value.get('CST', '') 
                        break

            # --- Lógica de Extração Robusta de COFINS ---
            cofins_data = imposto.get('COFINS', {})
            cofins_detalhe = {}
            cst_cofins = ''
            if cofins_data:
                for key, value in cofins_data.items():
                    if isinstance(value, dict):
                        cofins_detalhe = value
                        cst_cofins = value.get('CST', '') 
                        break

            # --- Mapeamento dos Dados ---
            ncm_valor = prod.get('NCM', '')
            # Certifique-se de que ClassificationType está definido ou use strings diretas
            tipo = 'SERVICO' if ncm_valor in ('00', '00000000') else 'PRODUTO' 
            
            item_data = {
                'nItem': item.get('@nItem', ''),
                'codigo_item': prod.get('cProd', ''),
                'descricao': prod.get('xProd', ''),
                'quantidade': float(prod.get('qCom', 0)),
                'valor_unitario': float(prod.get('vUnCom', 0)),
                'valor_total': float(prod.get('vProd', 0)),
                'tipo': tipo,
                'ncm': ncm_valor,
                'cfop': prod.get('CFOP', ''),
                                
                # Detalhes do ICMS
                'cst_csosn': cst_csosn_valor, # Usa a string corrigida
                'aliq_icms': float(icms_detalhe.get('pICMS', 0)),
                'vBC_icms': float(icms_detalhe.get('vBC', 0)),
                'vICMS': float(icms_detalhe.get('vICMS', 0)),
                'origem': icms_detalhe.get('orig', ''),
                
                # 🌟 Novos detalhes de IPI, PIS e COFINS
                'cst_ipi': cst_ipi,
                'vIPI': float(ipi_detalhe.get('vIPI', 0)),
                'aliq_ipi': float(ipi_detalhe.get('pIPI', 0)),
                
                'cst_pis': cst_pis,
                'vPIS': float(pis_detalhe.get('vPIS', 0)),
                
                'cst_cofins': cst_cofins,
                'vCOFINS': float(cofins_detalhe.get('vCOFINS', 0)),
            }
            
            itens.append(item_data)
        
        return itens
    
    def _extract_impostos(self, total: dict, inf_nfe: dict) -> list[dict]:
        """Extrai impostos da nota."""
        impostos = []
        
        # ICMS
        v_icms = float(total.get('vICMS', 0))
        v_bc = float(total.get('vBC', 0))
        aliq_icms_calc = round((v_icms / v_bc) * 100, 2) if v_bc > 0 else 0.0
        if v_icms > 0 or v_bc > 0:
            impostos.append({
                'tipo_imposto': 'ICMS',
                'valor_imposto': v_icms,
                'valor_base': v_bc,
                'aliquota': aliq_icms_calc, # Calcula a alíquota média
            })
            
        v_icms_st = float(total.get('vICMSST', 0))
        if v_icms_st > 0:
            impostos.append({
                'tipo_imposto': 'ICMS_ST',
                'valor_imposto': v_icms_st,
                'valor_base': float(total.get('vBCST', 0)),
                'aliquota': 0.0,
            })
        
        v_icms_deson = float(total.get('vICMSDeson', 0))
        if v_icms_deson > 0:
            impostos.append({
                'tipo_imposto': 'ICMS_DESON',
                'valor_imposto': v_icms_deson,
                'valor_base': 0.0,
                'aliquota': 0.0,
            })
        
        # IPI
        v_ipi = float(total.get('vIPI', 0))
        if v_ipi > 0:
            impostos.append({
                'tipo_imposto': 'IPI',
                'valor_imposto': v_ipi,
                'valor_base': 0.0,
                'aliquota': 0.0,
            })
        
        # PIS
        v_pis = float(total.get('vPIS', 0))
        if v_pis > 0:
            impostos.append({
                'tipo_imposto': 'PIS',
                'valor_imposto': v_pis,
                'valor_base': 0.0,
                'aliquota': 0.0,
            })
        
        # COFINS
        v_cofins = float(total.get('vCOFINS', 0))
        if v_cofins > 0:
            impostos.append({
                'tipo_imposto': 'COFINS',
                'valor_imposto': v_cofins,
                'valor_base': 0.0,
                'aliquota': 0.0,
            })
        
        return impostos
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Converte string de data para datetime."""
        try:
            # Formato: 2024-01-15T10:30:00-03:00
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
