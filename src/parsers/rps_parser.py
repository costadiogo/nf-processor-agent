"""Parser para RPS (Recibo Provisório de Serviços)."""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from src.constants import DocumentType, ClassificationType
from logs.logger import parser_logger


class RPSParser:
    """Parser para RPS/NFSe (Nota de Serviço)."""
    
    def __init__(self, file_path: str | Path):
        """Inicializa parser."""
        self.file_path = Path(file_path)
        self.data = None
        
    def parse(self) -> dict:
        """Faz parsing do arquivo XML RPS."""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            
            parser_logger.info(f"✅ Arquivo RPS lido: {self.file_path.name}")
            return self._extract_data(root)
            
        except Exception as e:
            parser_logger.error(f"❌ Erro ao ler RPS: {e}")
            raise
    
    def _extract_data(self, root: ET.Element) -> dict:
        """Extrai dados do RPS."""
        try:
            # Navegar na estrutura RPS
            nfse = root.find('.//Nfse')
            if nfse is None:
                nfse = root.find('.//CompNfse/Nfse')
            
            if nfse is None:
                raise ValueError("Estrutura RPS não reconhecida")
            
            inf_nfse = nfse.find('InfNfse')
            
            # Identificação
            numero = inf_nfse.find('Numero').text if inf_nfse.find('Numero') is not None else ''
            codigo_verificacao = inf_nfse.find('CodigoVerificacao').text if inf_nfse.find('CodigoVerificacao') is not None else ''
            data_emissao = inf_nfse.find('DataEmissao').text if inf_nfse.find('DataEmissao') is not None else ''
            
            # RPS
            ident_rps = inf_nfse.find('IdentificacaoRps')
            serie = '1'
            if ident_rps is not None:
                serie_elem = ident_rps.find('Serie')
                if serie_elem is not None:
                    serie = serie_elem.text
            
            # Serviço
            servico = inf_nfse.find('Servico')
            valores = servico.find('Valores') if servico is not None else None
            
            # Valores
            valor_servicos = float(valores.find('ValorServicos').text) if valores is not None and valores.find('ValorServicos') is not None else 0.0
            valor_iss = float(valores.find('ValorIss').text) if valores is not None and valores.find('ValorIss') is not None else 0.0
            aliquota = float(valores.find('Aliquota').text) if valores is not None and valores.find('Aliquota') is not None else 0.0
            base_calculo = float(valores.find('BaseCalculo').text) if valores is not None and valores.find('BaseCalculo') is not None else 0.0
            
            valor_pis = float(valores.find('ValorPis').text) if valores is not None and valores.find('ValorPis') is not None else 0.0
            valor_cofins = float(valores.find('ValorCofins').text) if valores is not None and valores.find('ValorCofins') is not None else 0.0
            valor_inss = float(valores.find('ValorInss').text) if valores is not None and valores.find('ValorInss') is not None else 0.0
            valor_ir = float(valores.find('ValorIr').text) if valores is not None and valores.find('ValorIr') is not None else 0.0
            valor_csll = float(valores.find('ValorCsll').text) if valores is not None and valores.find('ValorCsll') is not None else 0.0
            
            # Item de serviço
            item_lista_servico = servico.find('ItemListaServico').text if servico is not None and servico.find('ItemListaServico') is not None else ''
            discriminacao = servico.find('Discriminacao').text if servico is not None and servico.find('Discriminacao') is not None else ''
            codigo_municipio = servico.find('CodigoMunicipio').text if servico is not None and servico.find('CodigoMunicipio') is not None else ''
            
            # Prestador
            prestador = inf_nfse.find('PrestadorServico')
            ident_prestador = prestador.find('IdentificacaoPrestador') if prestador is not None else None
            cnpj_prestador = ident_prestador.find('Cnpj').text if ident_prestador is not None and ident_prestador.find('Cnpj') is not None else ''
            
            # Tomador
            tomador = inf_nfse.find('TomadorServico')
            ident_tomador = tomador.find('IdentificacaoTomador') if tomador is not None else None
            cpf_cnpj_tomador = ''
            if ident_tomador is not None:
                cpf_cnpj = ident_tomador.find('CpfCnpj')
                if cpf_cnpj is not None:
                    cnpj_elem = cpf_cnpj.find('Cnpj')
                    cpf_elem = cpf_cnpj.find('Cpf')
                    cpf_cnpj_tomador = cnpj_elem.text if cnpj_elem is not None else (cpf_elem.text if cpf_elem is not None else '')
            
            # Natureza da operação
            natureza_op = inf_nfse.find('NaturezaOperacao')
            natop = ''
            if natureza_op is not None:
                nat_code = natureza_op.text
                natop_map = {
                    '1': 'Tributação no município',
                    '2': 'Tributação fora do município',
                    '3': 'Isenção',
                    '4': 'Imune',
                    '5': 'Exigibilidade suspensa',
                    '6': 'Exportação de serviço'
                }
                natop = natop_map.get(nat_code, f'Natureza {nat_code}')
            
            cfop = '5933' if natureza_op.text == '1' else '6933'

            nf_data = {
                'numero_nf': numero,
                'serie': serie,
                'tipo_nf': DocumentType.RPS.value,
                'data_emissao': self._parse_datetime(data_emissao),
                'classificacao': ClassificationType.SERVICO.value,
                'cfop': cfop,
                'natop': natop,
                'sct': 'N',
                'valor_total': valor_servicos,
                'fornecedor_cnpj': cnpj_prestador,
                'cliente_cnpj': cpf_cnpj_tomador,
                'codigo_verificacao': codigo_verificacao,
                'item_lista_servico': item_lista_servico,
                'codigo_municipio': codigo_municipio,
                'itens': self._extract_itens(discriminacao, valor_servicos, item_lista_servico),
                'impostos': self._extract_impostos(
                    valor_iss, aliquota, base_calculo,
                    valor_pis, valor_cofins, valor_inss, valor_ir, valor_csll
                ),
            }
            
            parser_logger.info(f"✅ Dados extraídos do RPS {nf_data['numero_nf']}")
            return nf_data
            
        except Exception as e:
            parser_logger.error(f"❌ Erro ao extrair dados do RPS: {e}")
            raise
    
    def _extract_itens(self, discriminacao: str, valor_total: float, item_lista: str) -> list[dict]:
        """Extrai itens do serviço."""
        item_data = {
            'codigo_item': item_lista or '001',
            'descricao': discriminacao[:500] if discriminacao else 'Serviço prestado',
            'quantidade': 1.0,
            'valor_unitario': valor_total,
            'valor_total': valor_total,
            'tipo': ClassificationType.SERVICO.value,
            'ncm': None,  # Serviço não tem NCM
            'item_lista_servico': item_lista,
        }
        
        return [item_data]
    
    def _extract_impostos(
        self, 
        valor_iss: float, 
        aliquota: float, 
        base_calculo: float,
        valor_pis: float,
        valor_cofins: float,
        valor_inss: float,
        valor_ir: float,
        valor_csll: float
    ) -> list[dict]:
        """Extrai impostos do RPS."""
        impostos = []
        
        # ISS (principal imposto de serviço)
        if valor_iss > 0:
            impostos.append({
                'tipo_imposto': 'ISS',
                'valor_imposto': valor_iss,
                'valor_base': base_calculo,
                'aliquota': aliquota * 100,  # Converter para percentual
            })
        
        # PIS
        if valor_pis > 0:
            impostos.append({
                'tipo_imposto': 'PIS',
                'valor_imposto': valor_pis,
                'valor_base': base_calculo,
                'aliquota': 0.65 if valor_pis > 0 else 0,
            })
        
        # COFINS
        if valor_cofins > 0:
            impostos.append({
                'tipo_imposto': 'COFINS',
                'valor_imposto': valor_cofins,
                'valor_base': base_calculo,
                'aliquota': 3.0 if valor_cofins > 0 else 0,
            })
        
        # INSS
        if valor_inss > 0:
            impostos.append({
                'tipo_imposto': 'INSS',
                'valor_imposto': valor_inss,
                'valor_base': base_calculo,
                'aliquota': 0,
            })
        
        # IR
        if valor_ir > 0:
            impostos.append({
                'tipo_imposto': 'IR',
                'valor_imposto': valor_ir,
                'valor_base': base_calculo,
                'aliquota': 0,
            })
        
        # CSLL
        if valor_csll > 0:
            impostos.append({
                'tipo_imposto': 'CSLL',
                'valor_imposto': valor_csll,
                'valor_base': base_calculo,
                'aliquota': 0,
            })
        
        return impostos
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Converte string de data para datetime."""
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
