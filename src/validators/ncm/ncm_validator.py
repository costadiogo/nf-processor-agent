from logs.logger import app_logger

def validar_ncm(ncm: str) -> dict:
    """
    Valida NCM contra tabela oficial.
    
    Args:
        ncm: Código NCM ( dígitos)
    
    Returns:
        dict com resultado da validação
    """

    resultado = {
        "valido": False,
        "ncm": ncm,
        "erros": []
    }
    
    # Validar formato (4 dígitos)
    if not ncm or len(ncm) != 8 or ncm == None:
        resultado["erros"].append(f"NCM '{ncm}' deve ter exatamente 8 dígitos")
        return resultado
    
    if not ncm.isdigit():
        resultado["erros"].append(f"NCM '{ncm}' deve conter apenas números")
        return resultado
    
    # Tudo OK
    resultado["valido"] = True
    
    return resultado


def validar_ncm_itens(nf_data: dict) -> dict:
    """
    Valida todos os NCM's de uma nota fiscal.
    
    Args:
        nf_data: Dados da nota fiscal
    
    Returns:
        dict com resultado da validação
    """
    erros = []
    avisos = []
    
    # Validar NCM de cada item
    for idx, item in enumerate(nf_data.get('itens', []), 1):
        ncm_item = item.get('ncm', '')
        ncm_item = str(ncm_item).strip() if ncm_item is None else ''
        if ncm_item:
            resultado = validar_ncm(ncm_item)
            if not resultado["valido"]:
                for erro in resultado["erros"]:
                    erros.append(f"Item {idx}: {erro}")
                app_logger.error(f"❌ Item {idx} - NCM inválido: {ncm_item}")
    
    return {
        "valido": len(erros) == 0,
        "erros": erros,
        "avisos": avisos
    }