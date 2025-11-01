import json
import os

from logs.logger import app_logger

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSOSN = os.path.join(SCRIPT_DIR, 'csosn.json')
CST_ICMS = os.path.join(SCRIPT_DIR, 'cst_icms.json')
CST_IPI = os.path.join(SCRIPT_DIR, 'cst_ipi.json')
CST_PIS_COFINS = os.path.join(SCRIPT_DIR, 'cst_pis_cofins.json')
ORIGEM = os.path.join(SCRIPT_DIR, 'origem.json')
RULES_CFOP = os.path.join(SCRIPT_DIR, 'cfops_rules.json')
GENERAL_RULES = os.path.join(SCRIPT_DIR, 'cfop_rules_optimized.json')

def carregar_files() -> dict:
    """Carrega todos os arquivos JSON fiscais em um dicionário."""
    tables = {}
    files = {
        "csosn": CSOSN,
        "cst_icms": CST_ICMS,
        "cst_ipi": CST_IPI,
        "cst_pis_cofins": CST_PIS_COFINS,
        "origem": ORIGEM,
        "rules_cfop": RULES_CFOP,
        "general_rules": GENERAL_RULES
    }

    for name, path in files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        with open(path, encoding="utf-8") as f:
            try:
                tables[name] = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Erro ao ler {path}: {e}")

    return tables

def get_regime_key(emitente_crt: str) -> str:
    """Mapeia o CRT do Emitente para a chave de regra no JSON."""
    if emitente_crt in ('1', '2'):
        return "SIMPLES_NACIONAL"
    return "REGIME_NORMAL"

def validar_cst_nfe(nf_data: dict) -> dict:
    files = carregar_files()
    erros = []
    avisos = []
    
    resultado = {
        "valido": False,
        "erros": []
    }

    # pega a lista de itens (produtos)
    itens = nf_data.get("itens", [])
    if not itens:
        erros.append({"msg": "NF sem itens para validar", "campo": "itens", "severity": "error"})
        return {"valido": False, "erros": erros, "avisos": avisos}

    rules_all = files["general_rules"]
    emitente_crt = str(nf_data.get("crt", "")).strip()
    regime_key = get_regime_key(emitente_crt)

    for item in itens:
        cfop = str(item.get("cfop", "")).strip()
        grupo = cfop[:1] + "000"

        regra_base = rules_all.get("per_cfop", {}).get(cfop)
        if not regra_base:
            regra_base = rules_all.get("per_group", {}).get(grupo)
            
        if not regra_base:
            erros.append({
                "msg": f"CFOP {cfop} não tem regra definida.",
                "campo": f"cfop_item_{item.get('nItem')}",
                "severity": "error"
            })
            app_logger.warning(f"❌ CFOP {cfop} não tem regra definida.")
            continue
        
        regra_regime = regra_base.get(regime_key)
        if not regra_regime and regime_key != "REGIME_NORMAL":
            # Fallback para o Regime Normal se o SN não tiver regra explícita
            regra_regime = regra_base.get("REGIME_NORMAL", regra_base)
             
        if not regra_regime:
            # Se não encontrar nenhuma regra estruturada, usa a base como fallback
            regra_regime = regra_base

        # Campos do item
        cst_csosn = str(item.get("cst_csosn", "")).strip()
        cst_ipi = str(item.get("cst_ipi", "")).strip()
        cst_pis = str(item.get("cst_pis", "")).strip()
        cst_cofins = str(item.get("cst_cofins", "")).strip()

        aliq_icms = float(item.get("aliq_icms", 0) or 0)
        vICMS = float(item.get("vICMS", 0) or 0)
        aliq_ipi = float(item.get("aliq_ipi", 0) or 0)
        vIPI = float(item.get("vIPI", 0) or 0)
        vPIS = float(item.get("vPIS", 0) or 0)
        vCOFINS = float(item.get("vCOFINS", 0) or 0)

        # === ICMS ===
        icms_rule = regra_regime.get("icms", {})
        
        # 3. Validação de CST/CSOSN vs. CFOP (Ajustado)
        valid_csosn = icms_rule.get("csosn_validos", [])
        valid_cst = icms_rule.get("cst_validos", [])
        
        # Lógica de validação do código fiscal (CST ou CSOSN)
        is_code_valid = False
        if regime_key == "SIMPLES_NACIONAL":
            # SN usa CSOSN
            if cst_csosn in valid_csosn:
                is_code_valid = True
        else:
            # Regime Normal usa CST
            if cst_csosn in valid_cst:
                is_code_valid = True
        
        # Se o código fiscal (CST/CSOSN) não for válido para o regime
        if cst_csosn and not is_code_valid:
             erros.append({
                "msg": f"CST/CSOSN {cst_csosn} incoerente com CFOP {cfop} (Regime {regime_key})",
                "campo": f"cst_csosn_item_{item.get('nItem')}",
                "severity": "error"
            })
             app_logger.warning(f"❌ CST/CSOSN {cst_csosn} não condiz com CFOP {cfop}")
        
        # 4. Validação de Destaque vs. CFOP (Ajustado para permitir Isenção/Não Tributação)
        # Se o código for de Isenção (CST 40/41 ou CSOSN 300/400), o destaque ZERO é esperado.
        is_icms_desonerado = cst_csosn in ["40", "41", "300", "400"]
        is_icms_tributado_integralmente = cst_csosn in ["00", "101"]

        if is_icms_tributado_integralmente and vICMS == 0 and aliq_icms == 0:
            erros.append({
                "msg": f"CFOP {cfop} espera destaque de ICMS (CST {cst_csosn}), mas valores zerados.",
                "campo": f"icms_item_{item.get('nItem')}",
                "severity": "error"
            })
            app_logger.warning(f"❌ CFOP {cfop} espera destaque de ICMS, mas aliq/ICMS zerados")
        
        elif is_icms_desonerado and (vICMS > 0 or aliq_icms > 0):
             avisos.append({
                "msg": f"ICMS destacado ({vICMS}) em item com CST/CSOSN {cst_csosn} (Isenção/Não Trib.).",
                "campo": f"icms_item_{item.get('nItem')}",
                "severity": "warn"
            })


        # === IPI (Regra simples mantida, mas buscando CSTs expandidos no Regime correto) ===
        ipi_rule = regra_regime.get("ipi", {})
        allowed_ipi = ipi_rule.get("cst_validos", [])
        
        if ipi_rule.get("esperado"):
            if vIPI == 0 and aliq_ipi == 0:
                 # Erro de falta de destaque
                 erros.append({"msg": f"CFOP {cfop} espera IPI, mas nenhum valor/alíquota informado", "campo": f"ipi_item_{item.get('nItem')}", "severity": "error"})
            
            if allowed_ipi and cst_ipi not in allowed_ipi:
                 erros.append({"msg": f"CST IPI {cst_ipi} inválido para CFOP {cfop}. Esperava {allowed_ipi}", "campo": f"cst_ipi_item_{item.get('nItem')}", "severity": "error"})
                 
        else: # IPI Não Esperado
            if vIPI > 0:
                # Aviso se houver destaque, mas não era esperado (muito comum em revenda)
                avisos.append({"msg": f"CFOP {cfop} em geral não espera IPI, mas valor informado", "campo": f"ipi_item_{item.get('nItem')}", "severity": "warn"})
            
            if allowed_ipi and cst_ipi not in allowed_ipi:
                 # Erro se o CST IPI não for Isento/Outras
                 erros.append({"msg": f"CST IPI {cst_ipi} inválido para CFOP {cfop}. Esperava {allowed_ipi}", "campo": f"cst_ipi_item_{item.get('nItem')}", "severity": "error"})


        # === PIS/COFINS (Regra simples mantida, buscando CSTs expandidos no Regime correto) ===
        pis_rule = regra_regime.get("pis_cofins", {})
        allowed_pis = pis_rule.get("cst_validos", [])
        
        # 5. Validação PIS/COFINS
        if cst_pis and allowed_pis and cst_pis not in allowed_pis:
            erros.append({
                "msg": f"CST PIS {cst_pis} incoerente com CFOP {cfop} (Regime {regime_key}). Esperado {allowed_pis}",
                "campo": f"cst_pis_item_{item.get('nItem')}",
                "severity": "error"
            })
            app_logger.warning(f"❌ CST PIS {cst_pis} incoerente com CFOP {cfop}.")
            
        if cst_cofins and allowed_pis and cst_cofins not in allowed_pis:
            erros.append({
                "msg": f"CST COFINS {cst_cofins} incoerente com CFOP {cfop} (Regime {regime_key}). Esperado {allowed_pis}",
                "campo": f"cst_cofins_item_{item.get('nItem')}",
                "severity": "error"
            })
            app_logger.warning(f"❌ CST COFINS {cst_cofins} incoerente com CFOP {cfop}.")

    resultado = {
        "valido": len(erros) == 0,
        "erros": erros,
        "avisos": avisos
    }
    
    return resultado