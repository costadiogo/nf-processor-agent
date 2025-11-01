import re
import json
from pathlib import Path

# Configurações de Caminho
SCRIPT_DIR = Path(__file__).resolve().parent
CFOP_PATH = SCRIPT_DIR / "cfop_natop.json"
OUTPUT_GENERATED = SCRIPT_DIR / "cfop_rules_optimized.json" # Novo nome para o arquivo otimizado

# --- CSTs/CSOSNs Expandidos para Flexibilidade Fiscal ---
# Estas listas são mais amplas e aceitam benefícios fiscais (Isenção, Alíquota Zero, etc.)

ICMS_CST_NORMAL = ["00", "10", "20", "40", "41", "51", "60", "70", "90"] # 40/41 são cruciais
ICMS_CSOSN_SN = ["101", "102", "103", "201", "202", "300", "400", "500", "900"]

IPI_CST_VALIDOS = ["00", "01", "02", "03", "04", "05", "49", "50", "51", "52", "53", "54", "55", "99"]

# PIS/COFINS CSTs - Expandidos para incluir Alíquota Zero (04, 06), Isento (07), Suspensão (05)
PIS_COFINS_SAIDA = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "49", "99"]
PIS_COFINS_ENTRADA = ["50", "51", "52", "53", "54", "55", "56", "60", "61", "62", "63", "64", "65", "66", "67", "70", "71", "72", "73", "74", "75", "98", "99"]


# Heurísticas e Padrões (Mantidas do seu código original)
KEYWORDS = {
    "st": ["substituição tributária", "substituição tributária", "suportada por substituição tributária", "sujeita à substituição tributária", "sujeita à retenção do icms por substituição"],
    "isento": ["isenta", "isento", "imune", "não tributada", "não tributado", "sem cobrança de icms"],
    "exportacao": ["exporta", "exportação", "exportação de"],
    "importacao": ["importação", "importado", "importado diretamente"],
    "industrializacao": ["industrialização","industrializacao","produção","produtos industrializados","fabricação","fabricado"],
    "venda": ["venda", "saída", "remessa", "baixa de estoque"],
    "compra": ["compra", "entrada", "aquisição", "retorno", "devolução"],
    "ativo_imobilizado": ["ativo imobilizado", "imobilizado", "bens do ativo imobilizado"],
    "devolucao": ["devolução", "retorno de mercadoria", "retorno"],
    "consumo": ["uso ou consumo", "uso e consumo", "uso consumo", "consumo"],
    "servico": ["serviço", "prestação de serviço"]
}

SUGGESTIONS = {
    "icms_tributado": {"cst": ["00","10","20","70","90"], "csosn": ["101","102","900"], "esperado": True},
    "icms_st": {"cst": ["60","10"], "csosn": ["201","202","203","500"], "esperado": False},
    "icms_isento": {"cst": ["40","41","50","51"], "csosn": ["300","400"], "esperado": False},
    "ipi_tributado": {"cst": ["00","50","51","99"], "esperado": True},
    "ipi_isento": {"cst": ["52","53","54","55"], "esperado": False},
    "pis_tributado": {"cst": ["01","02"], "esperado": True},
    "pis_isento": {"cst": ["04","05","06","07","08","09","49"], "esperado": False}
}

def lower_strip(s): 
    return (s or "").lower().strip()

def infer_from_description(desc, cfop_code):
    """
    Inferencia de regras a partir da descrição do CFOP.
    Retorna regras brutas que serão refinadas na função 'generate'.
    """
    d = lower_strip(desc)
    res = {
        "tipo_operacao": None,
        "icms": {"esperado": None, "cst_validos": [], "csosn_validos": []},
        "ipi": {"esperado": None, "cst_validos": []},
        "pis_cofins": {"credito": None, "cst_validos": []},
        "observacoes": []
    }
    
    # 1. Tipo de operação
    is_entrada = cfop_code.startswith(("1", "2", "3")) or re.search(r"\b(entrada|compra|aquisiç|importa|retorno)\b", d)
    is_saida = cfop_code.startswith(("5", "6", "7")) or re.search(r"\b(venda|saída|saida|remessa|exporta|devolução)\b", d)

    if is_entrada and not is_saida:
        res["tipo_operacao"] = "entrada"
    elif is_saida and not is_entrada:
        res["tipo_operacao"] = "saida"
    else:
        res["tipo_operacao"] = "desconhecido"


    # 2. ICMS
    if any(k in d for k in KEYWORDS["st"]):
        res["icms"]["esperado"] = False
        res["icms"]["cst_validos"] = SUGGESTIONS["icms_st"]["cst"]
        res["icms"]["csosn_validos"] = SUGGESTIONS["icms_st"]["csosn"]
        res["observacoes"].append("provavel_substituicao_tributaria")
    elif any(k in d for k in KEYWORDS["isento"]):
        res["icms"]["esperado"] = False
        res["icms"]["cst_validos"] = SUGGESTIONS["icms_isento"]["cst"]
        res["icms"]["csosn_validos"] = SUGGESTIONS["icms_isento"]["csosn"]
        res["observacoes"].append("provavel_isencao")
    else:
        # Padrão: tributado ou potencial crédito
        res["icms"]["esperado"] = True
        res["icms"]["cst_validos"] = SUGGESTIONS["icms_tributado"]["cst"]
        res["icms"]["csosn_validos"] = SUGGESTIONS["icms_tributado"]["csosn"]

    # 3. IPI
    is_industrializacao = any(kw in d for kw in KEYWORDS["industrializacao"] + KEYWORDS["importacao"])
    
    if is_industrializacao:
        res["ipi"]["esperado"] = True
        res["ipi"]["cst_validos"] = SUGGESTIONS["ipi_tributado"]["cst"]
    elif any(kw in d for kw in KEYWORDS["consumo"] + KEYWORDS["exportacao"]):
        res["ipi"]["esperado"] = False
        res["ipi"]["cst_validos"] = SUGGESTIONS["ipi_isento"]["cst"]
    else:
        res["ipi"]["esperado"] = False # Default para revenda
        res["ipi"]["cst_validos"] = SUGGESTIONS["ipi_isento"]["cst"]

    # 4. PIS/COFINS
    if res["tipo_operacao"] == "saida":
        res["pis_cofins"]["credito"] = False
        res["pis_cofins"]["cst_validos"] = SUGGESTIONS["pis_tributado"]["cst"]
    elif res["tipo_operacao"] == "entrada":
        res["pis_cofins"]["credito"] = True
        res["pis_cofins"]["cst_validos"] = SUGGESTIONS["pis_isento"]["cst"]
    else:
        # Desconhecido: assume potencial crédito se for grupo de entrada
        res["pis_cofins"]["credito"] = is_entrada 
        res["pis_cofins"]["cst_validos"] = SUGGESTIONS["pis_isento"]["cst"]

    return res

def structure_and_expand_rules(inferred_rules):
    """
    Aplica a segregação por Regime Tributário e expande as listas de CST/CSOSN
    com base nas regras globais.
    """
    optimized_rules = {}

    for cfop, rules in inferred_rules.items():
        is_entrada = rules["tipo_operacao"] == "entrada" or cfop.startswith(("1", "2", "3"))
        is_saida = rules["tipo_operacao"] == "saida" or cfop.startswith(("5", "6", "7"))
        
        # Define as listas de CST/CSOSN globais baseadas na direção (Entrada/Saída)
        icms_cst = ICMS_CST_NORMAL
        ipi_cst = IPI_CST_VALIDOS
        pis_cofins_cst_normal = PIS_COFINS_ENTRADA if is_entrada else PIS_COFINS_SAIDA
        pis_cofins_cst_sn = PIS_COFINS_ENTRADA if is_entrada else PIS_COFINS_SAIDA # Simples Nacional também usa CSTs para PIS/COFINS
        
        # Combina CSTs inferidos com a lista global expandida para ter certeza que as exceções passam
        combined_icms_cst = sorted(list(set(icms_cst) | set(rules["icms"]["cst_validos"])))
        combined_ipi_cst = sorted(list(set(ipi_cst) | set(rules["ipi"]["cst_validos"])))
        combined_pis_cofins_cst = sorted(list(set(pis_cofins_cst_normal) | set(rules["pis_cofins"]["cst_validos"])))


        # --- 1. REGIME NORMAL (CRT 3) ---
        regime_normal_rules = {
            "icms": {
                "esperado": rules["icms"]["esperado"],
                "cst_validos": combined_icms_cst
            },
            "ipi": {
                "esperado": rules["ipi"]["esperado"],
                "cst_validos": combined_ipi_cst
            },
            "pis_cofins": {
                "credito": is_entrada,
                "cst_validos": combined_pis_cofins_cst
            }
        }

        # --- 2. SIMPLES NACIONAL (CRT 1 ou 2) ---
        # No Simples Nacional, ICMS usa CSOSN e IPI/PIS/COFINS usam CSTs.
        simples_nacional_rules = {
            "icms": {
                "esperado": rules["icms"]["esperado"],
                "csosn_validos": ICMS_CSOSN_SN 
            },
            "ipi": {
                "esperado": rules["ipi"]["esperado"],
                "cst_validos": ["53", "55", "99"] # Simplificando IPI no SN (geralmente Isento)
            },
            "pis_cofins": {
                "credito": is_entrada,
                "cst_validos": ["04", "05", "06", "07", "49", "99"] # PIS/COFINS é normalmente 49, 07 ou 04 no SN
            }
        }

        optimized_rules[cfop] = {
            "tipo_operacao": rules["tipo_operacao"],
            "observacoes": ["Regras segregadas por CRT e CSTs/CSOSNs expandidos para maior flexibilidade fiscal. (Gerado por script)"],
            "REGIME_NORMAL": regime_normal_rules,
            "SIMPLES_NACIONAL": simples_nacional_rules
        }

    return optimized_rules

def generate():
    with open(CFOP_PATH, encoding="utf-8") as f:
        cfop_table = json.load(f)

    inferred_output = {}
    
    # 1. Inferir regras brutas
    for code, desc in cfop_table.items():
        inferred_output[code] = infer_from_description(desc, code)

    # 2. Estruturar e expandir as regras inferidas (aplicando a segregação de regime)
    optimized_per_cfop = structure_and_expand_rules(inferred_output)
    
    # 3. Construir as regras de grupo (per_group)
    groups = {}
    for code, rules in optimized_per_cfop.items():
        group = code[0]
        # Aqui, vamos usar apenas as regras de REGIME_NORMAL como base para o grupo
        g_rules = rules["REGIME_NORMAL"]
        
        g = groups.setdefault(group, {"icms_esperado":0,"ipi_esperado":0,"pis_credito":0,"count":0})
        g["count"] += 1
        if g_rules["icms"]["esperado"]: g["icms_esperado"] += 1
        if g_rules["ipi"]["esperado"]: g["ipi_esperado"] += 1
        if g_rules["pis_cofins"]["credito"]: g["pis_credito"] += 1

    final_groups = {}
    for g, s in groups.items():
        # maioria simples
        icms_expected = s["icms_esperado"] > (s["count"]/2)
        ipi_expected = s["ipi_esperado"] > (s["count"]/2)
        pis_credito = s["pis_credito"] > (s["count"]/2)
        
        final_groups[g + "000"] = {
            "tipo_operacao": ("entrada" if g in ["1","2","3"] else "saida"),
            "icms": {"esperado": icms_expected},
            "ipi": {"esperado": ipi_expected},
            "pis_cofins": {"credito": pis_credito}
        }

    # 4. Salvar o arquivo final
    generated = {
        "per_cfop": optimized_per_cfop,
        "per_group": final_groups
    }
    with open(OUTPUT_GENERATED, "w", encoding="utf-8") as f:
        json.dump(generated, f, indent=2, ensure_ascii=False)
    print(f"Gerado: {OUTPUT_GENERATED}")

if __name__ == "__main__":
    # Supondo que 'cfop_natop.json' exista no mesmo diretório
    # Se 'cfop_natop.json' não existir, este script falhará, mas a lógica está correta.
    generate()
