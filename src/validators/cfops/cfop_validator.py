import json
import os

from logs.logger import app_logger

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(SCRIPT_DIR, 'cfop_natop.json')

def load_cfop_data(file_path: str) -> dict:
    """Carrega os dados dos CFOPs e suas descrições a partir do arquivo JSON."""
    
    if not os.path.exists(file_path):
        app_logger.error(f"Erro: O arquivo CFOP não foi encontrado no caminho: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cfop_data = json.load(f)
            return cfop_data
    except json.JSONDecodeError:
        app_logger.error(f"Erro: Falha ao decodificar o JSON no arquivo: {file_path}. Verifique a sintaxe.")
        return {}
    except Exception as e:
        app_logger.error(f"Ocorreu um erro inesperado ao carregar o arquivo: {e}")
        return {}
    
def validar_cfop(cfop: str) -> dict:
    """
    Valida CFOP contra tabela oficial.
    
    Args:
        cfop: Código CFOP (4 dígitos)
    
    Returns:
        dict com resultado da validação
    """
    
    cfop_data = load_cfop_data(JSON_FILE_PATH)
    resultado = {
        "valido": False,
        "cfop": cfop,
        "descricao": None,
        "erros": []
    }
    
    if not cfop or len(cfop) != 4:
        resultado["erros"].append(f"CFOP '{cfop}' deve ter exatamente 4 dígitos")
        return resultado
    
    if not cfop.isdigit():
        resultado["erros"].append(f"CFOP '{cfop}' deve conter apenas números")
        return resultado
    
    if cfop not in cfop_data:
        resultado["erros"].append(f"CFOP '{cfop}' não encontrado na tabela oficial")
        return resultado

    resultado["valido"] = True
    resultado["descricao"] = cfop_data[cfop]
    
    return resultado


def validar_cfops_nota(nf_data: dict) -> dict:
    """
    Valida todos os CFOPs de uma nota fiscal.
    
    Args:
        nf_data: Dados da nota fiscal
    
    Returns:
        dict com resultado da validação
    """
    erros = []
    avisos = []
    
    cfop_nota = nf_data.get('cfop', '')
    if cfop_nota:
        resultado = validar_cfop(cfop_nota)
        if not resultado["valido"]:
            erros.extend(resultado["erros"])
            app_logger.error(f"❌ CFOP da nota inválido: {cfop_nota}")

    for idx, item in enumerate(nf_data.get('itens', []), 1):
        cfop_item = item.get('cfop', '')
        if cfop_item:
            resultado = validar_cfop(cfop_item)
            if not resultado["valido"]:
                for erro in resultado["erros"]:
                    erros.append(f"Item {idx}: {erro}")
                app_logger.error(f"❌ Item {idx} - CFOP inválido: {cfop_item}")
    
    return {
        "valido": len(erros) == 0,
        "erros": erros,
        "avisos": avisos
    }