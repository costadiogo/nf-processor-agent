from logs.logger import app_logger

def validar_dest(nf_data: dict) -> str:
    
    # Validar cnpj da nota
    cnpj = nf_data.get('cliente_cnpj')
    cpf = nf_data.get('cliente_cpf')
    
    if cnpj and not cpf:
        return "PJ"
    elif cpf and not cnpj:
        return "PF"
    elif not cnpj and not cpf:
        return "AUSENTE"
    else:
        return "INDEFINIDO"
    

def validar_cpf(cpf: str) -> dict:
    """
    Valida CPF contra tabela oficial.
    
    Args:
        cpf: Código CPF ( dígitos)
    
    Returns:
        dict com resultado da validação
    """

    resultado = {
        "valido": False,
        "cpf": cpf,
        "erros": []
    }
    
    # Validar formato (11 dígitos)
    if not cpf or len(cpf) != 11:
        resultado["erros"].append(f"CPF '{cpf}' deve ter exatamente 11 dígitos")
        return resultado
    
    if not cpf.isdigit():
        resultado["erros"].append(f"CPF '{cpf}' deve conter apenas números")
        return resultado
    
    # Tudo OK
    resultado["valido"] = True
    
    return resultado


def validar_cnpj(cnpj: str) -> dict:
    """
    Valida CPF contra tabela oficial.
    
    Args:
        cpf: Código CPF ( dígitos)
    
    Returns:
        dict com resultado da validação
    """

    resultado = {
        "valido": False,
        "cnpj": cnpj,
        "erros": []
    }
    
    # Validar formato (14 dígitos)
    if not cnpj or len(cnpj) != 14:
        resultado["erros"].append(f"CNPJ '{cnpj}' deve ter exatamente 11 dígitos")
        return resultado
    
    if not cnpj.isdigit():
        resultado["erros"].append(f"CNPJ '{cnpj}' deve conter apenas números")
        return resultado
    
    # Tudo OK
    resultado["valido"] = True
    
    return resultado


def validar_document_dest(nf_data: dict) -> dict:
    erros = []
    avisos = []
    
    dest = validar_dest(nf_data)
    
    if dest == "PJ":
        cnpj = nf_data['cliente_cnpj']
        resultado = validar_cnpj(cnpj)
        if not resultado["valido"]:
            erros.extend(resultado["erros"])
    elif dest == "PF":
        cpf = nf_data['cliente_cpf']
        resultado = validar_cpf(cpf)
        if not resultado["valido"]:
            erros.extend(resultado["erros"])
    elif dest == "AUSENTE":
        erros.append("CNPJ ou CPF do destinatário estão ausentes")
        app_logger.error("❌ CNPJ ou CPF do destinatário estão ausentes")
    elif dest == "INDEFINIDO":
        erros.append("Ambos CNPJ ou CPF do destinatário não estão preenchidos")
        app_logger.error("❌ Ambos CNPJ ou CPF do destinatário não estão preenchidos")

  
    return {
        "valido": len(erros) == 0,
        "erros": erros,
        "avisos": avisos
    }