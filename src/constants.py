"""
Constantes globais da aplicação NFe Processor Agent.

Este módulo define todas as constantes utilizadas em toda a aplicação,
como CFOP válidos, tipos de impostos, tipos de documentos, etc.
"""

from enum import Enum
from typing import Final

# =====================================================
# CONSTANTES DE TIPOS DE DOCUMENTO
# =====================================================

class DocumentType(str, Enum):
    """Tipos de documentos fiscais suportados."""
    NFE = "NFe"  # Nota Fiscal Eletrônica
    RPS = "RPS"  # Recibo de Serviço
    NFC_E = "NFCe"  # Nota Fiscal do Consumidor Eletrônica
    CT_E = "CTe"  # Conhecimento de Transporte Eletrônico


# =====================================================
# CONSTANTES DE CLASSIFICAÇÃO
# =====================================================

class ClassificationType(str, Enum):
    """Classificação de itens em nota fiscal."""
    PRODUTO = "Produto"
    SERVICO = "Serviço"
    AMBOS = "Produtos e Serviços"


# =====================================================
# CONSTANTES DE CFOP (Código Fiscal de Operação)
# =====================================================

# CFOPs válidos para Produtos (entrada e saída)
CFOP_ENTRADA_PRODUTO: Final[dict[str, str]] = {
    "1100": "Compra para industrialização",
    "1101": "Compra para comercialização",
    "1102": "Devolução de venda",
    "1103": "Aquisição de serviço de transporte",
    "1104": "Aquisição de serviço de comunicação",
    "1105": "Aquisição de energia elétrica",
    "1106": "Aquisição para revenda",
    "1107": "Aquisição em operação de FIFO",
    "1108": "Aquisição em transferência para industrialização",
    "1109": "Aquisição em transferência para revenda",
    "1110": "Aquisição de ativo imobilizado",
    "1111": "Aquisição de ativo imobilizado para revenda",
    "1112": "Entrada de matéria-prima",
}

CFOP_SAIDA_PRODUTO: Final[dict[str, str]] = {
    "5100": "Venda de mercadoria",
    "5101": "Venda de mercadoria com ICMS substituído",
    "5102": "Devolução de compra",
    "5103": "Transferência de mercadoria",
    "5104": "Devolução de transferência",
    "5105": "Venda de sucata",
    "5106": "Venda de ativo imobilizado",
    "5107": "Venda de bem do ativo imobilizado",
    "5108": "Venda de amostra",
    "5109": "Venda de amostra grátis",
    "5110": "Venda de brinde",
    "5111": "Venda de conjuntos de brindes",
    "5112": "Venda de embalagem",
}

# CFOPs válidos para Serviços
CFOP_ENTRADA_SERVICO: Final[dict[str, str]] = {
    "3100": "Compra de serviço",
    "3101": "Compra de serviço de transporte",
    "3102": "Compra de serviço de comunicação",
    "3103": "Compra de energia elétrica",
    "3104": "Compra de serviço de consultoria",
    "3105": "Compra de serviço de manutenção",
}

CFOP_SAIDA_SERVICO: Final[dict[str, str]] = {
    "5300": "Venda de serviço",
    "5301": "Venda de serviço de transporte",
    "5302": "Venda de serviço de comunicação",
    "5303": "Venda de energia elétrica",
    "5304": "Venda de serviço de consultoria",
    "5305": "Venda de serviço de manutenção",
}

# Todos os CFOPs válidos
CFOP_VALIDOS: Final[list[str]] = [
    *CFOP_ENTRADA_PRODUTO.keys(),
    *CFOP_SAIDA_PRODUTO.keys(),
    *CFOP_ENTRADA_SERVICO.keys(),
    *CFOP_SAIDA_SERVICO.keys(),
]


# =====================================================
# CONSTANTES DE NATOP (Natureza da Operação)
# =====================================================

NATOP_VALORES: Final[dict[str, str]] = {
    "01": "Venda de produção do estabelecimento",
    "02": "Venda de mercadoria adquirida",
    "03": "Venda de serviço",
    "04": "Retorno/devolução de compra",
    "05": "Retorno/devolução de venda",
    "06": "Transferência de estoque",
    "07": "Transferência de produção",
    "08": "Industrialização",
    "09": "Industrialização para terceiros",
    "10": "Entrada de estoque",
    "11": "Compra de armazenagem",
    "12": "Compra de reparo",
    "13": "Outros",
    "14": "Operação com suspensão de ICMS",
    "15": "Operação com substituição tributária",
    "16": "Operação isenta de ICMS",
    "17": "Operação sem incidência de ICMS",
    "18": "Exportação de produção",
    "19": "Exportação de mercadoria",
}


# =====================================================
# CONSTANTES DE TIPOS DE IMPOSTO
# =====================================================

class TaxType(str, Enum):
    """Tipos de impostos calculados."""
    ICMS = "ICMS"  # Imposto sobre Circulação de Mercadorias e Serviços
    IPI = "IPI"    # Imposto sobre Produtos Industrializados
    PIS = "PIS"    # Programa de Integração Social
    COFINS = "COFINS"  # Contribuição para Financiamento da Seguridade Social
    ISS = "ISS"    # Imposto sobre Serviços
    IRPJ = "IRPJ"  # Imposto de Renda Pessoa Jurídica
    CSLL = "CSLL"  # Contribuição Social sobre o Lucro Líquido
    INSS = "INSS"  # Instituto Nacional do Seguro Social


# Tipos de ICMS
class ICMSType(str, Enum):
    """Tipos de ICMS."""
    NORMAL = "ICMS Normal"
    ST = "ICMS Substituição Tributária"
    ISENTO = "ICMS Isento"
    NAO_TRIBUTADO = "ICMS Não Tributado"
    DIFERENCIADO = "ICMS Diferenciado"
    PARTILHA = "ICMS Partilha"


# =====================================================
# CONSTANTES DE SCT (Sistema Certificação Técnica)
# =====================================================

SCT_VALIDOS: Final[list[str]] = [
    "N",  # Não
    "S",  # Sim
    "101",  # Lei 14.016 de 6 de junho de 2020
]


# =====================================================
# CONSTANTES DE STATUS DE PROCESSAMENTO
# =====================================================

class ProcessingStatus(str, Enum):
    """Status de processamento de nota fiscal."""
    PENDENTE = "Pendente"
    PROCESSANDO = "Processando"
    VALIDO = "Válido"
    ERRO = "Erro"
    AVISO = "Aviso"
    COMPLETO = "Completo"


# =====================================================
# CONSTANTES DE MENSAGENS
# =====================================================

MENSAGENS: Final[dict[str, str]] = {
    # Sucesso
    "success_import": "✅ Nota fiscal importada com sucesso",
    "success_validation": "✅ Validação realizada com sucesso",
    "success_calculation": "✅ Cálculo de impostos realizado com sucesso",
    "success_save": "✅ Dados salvos com sucesso",
    
    # Erro
    "error_file_not_found": "❌ Arquivo não encontrado",
    "error_invalid_format": "❌ Formato de arquivo inválido",
    "error_parsing": "❌ Erro ao fazer parsing do arquivo",
    "error_validation": "❌ Erro na validação de campos",
    "error_database": "❌ Erro ao acessar banco de dados",
    "error_llm": "❌ Erro ao comunicar com LLM",
    
    # Avisos
    "warning_incomplete_data": "⚠️ Dados incompletos detectados",
    "warning_missing_field": "⚠️ Campo obrigatório faltando",
    "warning_inconsistency": "⚠️ Inconsistência detectada",
}


# =====================================================
# CONSTANTES DE LIMITES E TAMANHOS
# =====================================================

# Tamanho máximo de campo
MAX_FIELD_SIZE: Final[int] = 500

# Comprimento máximo de número de nota
MAX_NF_NUMBER_LENGTH: Final[int] = 9

# Comprimento máximo de série
MAX_SERIES_LENGTH: Final[int] = 3

# Comprimento de CFOP
CFOP_LENGTH: Final[int] = 4

# Comprimento de NATOP
NATOP_LENGTH: Final[int] = 2


# =====================================================
# CONSTANTES DE REGEX PATTERNS
# =====================================================

import re

# Pattern para validar número de NF (1 a 9 dígitos)
PATTERN_NF_NUMBER: Final[str] = r"^\d{1,9}$"

# Pattern para validar série (1 a 3 caracteres)
PATTERN_SERIE: Final[str] = r"^[0-9A-Za-z]{1,3}$"

# Pattern para validar CFOP (4 dígitos)
PATTERN_CFOP: Final[str] = r"^\d{4}$"

# Pattern para validar NATOP (2 dígitos)
PATTERN_NATOP: Final[str] = r"^\d{2}$"

# Pattern para validar CNPJ (14 dígitos)
PATTERN_CNPJ: Final[str] = r"^\d{14}$"

# Pattern para validar CPF (11 dígitos)
PATTERN_CPF: Final[str] = r"^\d{11}$"

# Pattern para validar email
PATTERN_EMAIL: Final[str] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Pattern para validar data ISO (YYYY-MM-DD)
PATTERN_DATE_ISO: Final[str] = r"^\d{4}-\d{2}-\d{2}$"

# Pattern para validar hora (HH:MM:SS)
PATTERN_TIME: Final[str] = r"^\d{2}:\d{2}:\d{2}$"


# =====================================================
# CONSTANTES DE FORMATO
# =====================================================

# Formato de data padrão
DATE_FORMAT: Final[str] = "%Y-%m-%d"

# Formato de hora padrão
TIME_FORMAT: Final[str] = "%H:%M:%S"

# Formato de data e hora padrão
DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Formato para exibição de valores monetários
CURRENCY_FORMAT: Final[str] = "R$ {:.2f}"


# =====================================================
# FUNÇÃO AUXILIAR PARA VALIDAR CFOP
# =====================================================

def is_valid_cfop(cfop: str) -> bool:
    """
    Verifica se o CFOP é válido.
    
    Args:
        cfop: Código CFOP a validar
        
    Returns:
        bool: True se CFOP é válido, False caso contrário
    """
    if not re.match(PATTERN_CFOP, cfop):
        return False
    return cfop in CFOP_VALIDOS


def is_valid_natop(natop: str) -> bool:
    """
    Verifica se o NATOP é válido.
    
    Args:
        natop: Código NATOP a validar
        
    Returns:
        bool: True se NATOP é válido, False caso contrário
    """
    if not re.match(PATTERN_NATOP, natop):
        return False
    return natop in NATOP_VALORES.keys()


def is_valid_sct(sct: str) -> bool:
    """
    Verifica se o SCT é válido.
    
    Args:
        sct: Código SCT a validar
        
    Returns:
        bool: True se SCT é válido, False caso contrário
    """
    return sct in SCT_VALIDOS


# =====================================================
# Teste ao executar diretamente
# =====================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📋 CONSTANTES CARREGADAS")
    print("=" * 60)
    print(f"✓ CFOPs válidos: {len(CFOP_VALIDOS)}")
    print(f"✓ NATOP válidos: {len(NATOP_VALORES)}")
    print(f"✓ Tipos de imposto: {len(TaxType)}")
    print(f"✓ Mensagens: {len(MENSAGENS)}")
    print("\n📋 EXEMPLOS:")
    print(f"  CFOP 5100: {CFOP_SAIDA_PRODUTO.get('5100')}")
    print(f"  NATOP 01: {NATOP_VALORES.get('01')}")
    print(f"  CFOP 5100 válido? {is_valid_cfop('5100')}")
    print(f"  CFOP 9999 válido? {is_valid_cfop('9999')}")
    print("=" * 60 + "\n")