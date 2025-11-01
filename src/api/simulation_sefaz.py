"""Simulador de homologação SEFAZ integrado ao workflow."""

import random
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

from logs.logger import agent_logger


class SefazSimulator:
    """Simulador de ambiente de homologação SEFAZ."""
    
    def __init__(self):
        """Inicializa simulador."""
        agent_logger.info("🏢 Simulador SEFAZ inicializado")
    
    def _generate_nfe_key(self, xml_content: str) -> str:
        """
        Gera chave NFe fictícia de 44 dígitos.
        Estrutura: cUF(2) + AAMM(4) + CNPJ(14) + mod(2) + serie(3) + nNF(9) + tpEmis(1) + cNF(8) + DV(1)
        
        Args:
            xml_content: Conteúdo XML da NFe
        
        Returns:
            Chave de 44 dígitos
        """
        try:
            root = ET.fromstring(xml_content)
            namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Extrair cUF (código UF)
            cuf_element = root.find('.//nfe:ide/nfe:cUF', namespaces)
            cuf = cuf_element.text if cuf_element is not None and cuf_element.text else "35"
            cuf = cuf.zfill(2)[:2]
            
            dhemi_element = root.find('.//nfe:ide/nfe:dhEmi', namespaces)
            aamm = datetime.datetime.now().strftime("%y%m")
            if dhemi_element is not None and dhemi_element.text:
                try:
                    dt_obj = datetime.datetime.fromisoformat(dhemi_element.text.replace('Z', '+00:00'))
                    aamm = dt_obj.strftime("%y%m")
                except:
                    pass
            
            cnpj_element = root.find('.//nfe:emit/nfe:CNPJ', namespaces)
            cnpj = cnpj_element.text if cnpj_element is not None and cnpj_element.text else ""
            cnpj = cnpj.zfill(14)[:14]  # Garantir 14 dígitos
            
            if len(cnpj) != 14:
                cnpj = ''.join(random.choices('0123456789', k=14))
            
            mod_element = root.find('.//nfe:ide/nfe:mod', namespaces)
            mod = mod_element.text if mod_element is not None and mod_element.text else "55"
            mod = mod.zfill(2)[:2]

            serie_element = root.find('.//nfe:ide/nfe:serie', namespaces)
            serie = serie_element.text if serie_element is not None and serie_element.text else "1"
            serie = serie.zfill(3)[:3]
            
            nnf_element = root.find('.//nfe:ide/nfe:nNF', namespaces)
            nnf = nnf_element.text if nnf_element is not None and nnf_element.text else "1"
            nnf = nnf.zfill(9)[:9]

            tpemis = "1"
            
            cnf = ''.join(random.choices('0123456789', k=8))
            
            chave_sem_dv = f"{cuf}{aamm}{cnpj}{mod}{serie}{nnf}{tpemis}{cnf}"
            
            if len(chave_sem_dv) > 43:
                chave_sem_dv = chave_sem_dv[:43]
            elif len(chave_sem_dv) < 43:
                chave_sem_dv = chave_sem_dv + '0' * (43 - len(chave_sem_dv))
            
            dv = self._calcular_dv(chave_sem_dv)
            
            chave_completa = f"{chave_sem_dv}{dv}"
            
            agent_logger.info(f"🔑 Chave NFe gerada: {chave_completa}")
            return chave_completa
            
        except Exception as e:
            agent_logger.warning(f"⚠️  Erro ao gerar chave realista, usando aleatória: {e}")
            chave = ''.join(random.choices('0123456789', k=44))
            return chave
    
    def _calcular_dv(self, chave: str) -> str:
        """
        Calcula dígito verificador usando módulo 11.
        
        Args:
            chave: Chave com 43 dígitos
        
        Returns:
            Dígito verificador (1 caractere)
        """
        try:
            multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
            soma = 0
            pos_mult = 0
            
            for i in range(len(chave) - 1, -1, -1):
                digito = int(chave[i])
                soma += digito * multiplicadores[pos_mult % 8]
                pos_mult += 1
            
            resto = soma % 11
            dv = 0 if resto in [0, 1] else 11 - resto
            
            return str(dv)
            
        except:
            return str(random.randint(0, 9))
    
    def simulate_submission(self, xml_path: str | Path) -> dict:
        """
        Simula submissão ao SEFAZ de homologação.
        
        Args:
            xml_path: Caminho do arquivo XML validado
        
        Returns:
            dict com resposta da simulação
        """
        try:
            # Ler XML
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            agent_logger.info(f"📤 Simulando envio ao SEFAZ: {Path(xml_path).name}")
            
            chave_nfe = self._generate_nfe_key(xml_content)
            
            nrec = ''.join(random.choices('0123456789', k=15))
            
            dh_recebimento = datetime.datetime.now().isoformat(timespec='seconds') + "-03:00"
            
            response = {
                "status": "sucesso",
                "codigo_status": "100",
                "motivo": "Autorizado o uso da NF-e",
                "chave_nfe": chave_nfe,
                "numero_protocolo": nrec,
                "data_recebimento": dh_recebimento,
                "mensagem": "✅ NFe AUTORIZADA - Arquivo validado e aprovado para uso em produção",
                "ambiente": "homologacao",
                "versao_app": "SEFAZ-Simulator-1.0"
            }
            
            agent_logger.info(f"✅ NFe autorizada - Chave: {chave_nfe}")
            
            return response
            
        except Exception as e:
            agent_logger.error(f"❌ Erro na simulação SEFAZ: {e}")
            
            return {
                "status": "erro",
                "codigo_status": "999",
                "motivo": f"Erro na simulação: {str(e)}",
                "chave_nfe": None,
                "numero_protocolo": None,
                "data_recebimento": None,
                "mensagem": f"❌ Erro ao processar: {str(e)}",
                "ambiente": "homologacao",
                "versao_app": "SEFAZ-Simulator-1.0"
            }
    
    def simulate_rejection(self, motivo: str = "Erro genérico") -> dict:
        """
        Simula uma rejeição do SEFAZ.
        
        Args:
            motivo: Motivo da rejeição
        
        Returns:
            dict com resposta de rejeição
        """
        codigos_rejeicao = {
            "202": "Rejeição: NF-e já está denegada na base de dados da SEFAZ",
            "217": "Rejeição: NF-e não consta na base de dados da SEFAZ",
            "227": "Rejeição: A data de emissão não pode ser anterior a data de emissão da NF referenciada",
            "229": "Rejeição: IE do destinatário não cadastrada",
            "248": "Rejeição: NF referenciada de produtor inexistente",
            "301": "Rejeição: Uso denegado : Irregularidade fiscal do emitente",
            "539": "Rejeição: CNPJ Emitente não cadastrado",
            "593": "Rejeição: Duplicidade de NF-e"
        }
        
        codigo = random.choice(list(codigos_rejeicao.keys()))
        
        return {
            "status": "rejeitado",
            "codigo_status": codigo,
            "motivo": codigos_rejeicao[codigo],
            "chave_nfe": None,
            "numero_protocolo": None,
            "data_recebimento": datetime.datetime.now().isoformat(timespec='seconds') + "-03:00",
            "mensagem": f"❌ NFe REJEITADA - {codigos_rejeicao[codigo]}",
            "ambiente": "homologacao",
            "versao_app": "SEFAZ-Simulator-1.0"
        }

