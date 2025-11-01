import json
import os

# --- 1. Regras de CST/CSOSN Expandidas para Flexibilizar a Validação ---

# CSTs de ICMS para Regime Normal (CRT 3) - Expandido para incluir 40, 41 (Isenção, Não Tributada)
ICMS_CST_SAIDA = ["00", "10", "20", "40", "41", "60", "70", "90"]
ICMS_CST_ENTRADA = ["00", "10", "20", "40", "41", "60", "70", "90", "50", "51"] # Adicionando 50/51 para Suspensão/Diferimento

# CSOSNs de ICMS para Simples Nacional (CRT 1/2) - Expandido para incluir 500/400 (ST, Isenção)
ICMS_CSOSN_VALIDOS = ["101", "102", "103", "201", "202", "300", "400", "500", "900"]

# CSTs de PIS/COFINS - Expandido para incluir Alíquota Zero (04/06), Isento (07), e Outras (99/49)
PIS_COFINS_CST_SAIDA = ["01", "02", "04", "05", "06", "07", "08", "09", "49", "99"]
PIS_COFINS_CST_ENTRADA = ["50", "51", "52", "53", "54", "55", "56", "60", "61", "62", "63", "64", "65", "66", "67", "70", "71", "72", "73", "74", "75", "98", "99"] # Lista completa de CSTs de crédito

# CSTs de IPI - Flexível para Saída (Revenda)
IPI_CST_SAIDA = ["52", "53", "54", "55", "99"]
IPI_CST_ENTRADA = ["00", "01", "02", "50", "51", "52", "53", "54", "55", "99"] # 00/01/02 para crédito na entrada

# --- 2. Função de Otimização ---

def optimize_cfop_rules(data):
    """
    Refatora as regras do CFOP para segregar por Regime Tributário
    e expandir as listas de CST/CSOSN.
    """
    optimized_data = {"per_cfop": {}}
    
    # Processa cada CFOP
    for cfop, rules in data.get("per_cfop", {}).items():
        tipo_operacao = rules.get("tipo_operacao", "desconhecido")
        is_entrada = tipo_operacao in ("entrada", "desconhecido") or cfop.startswith(("1", "2", "3"))
        is_saida = tipo_operacao == "saida" or cfop.startswith(("5", "6", "7"))
        
        # 1. Definir listas de impostos expandidas
        icms_cst = ICMS_CST_ENTRADA if is_entrada else ICMS_CST_SAIDA
        pis_cofins_cst = PIS_COFINS_CST_ENTRADA if is_entrada else PIS_COFINS_CST_SAIDA
        ipi_cst = IPI_CST_ENTRADA if is_entrada else IPI_CST_SAIDA
        
        # Garantir que CSTs rígidos originais estejam contidos
        original_icms_cst = rules.get("icms", {}).get("cst_validos", [])
        icms_cst = sorted(list(set(icms_cst) | set(original_icms_cst)))
        
        # 2. Construir o novo objeto otimizado
        new_rules = {
            "tipo_operacao": tipo_operacao,
            "observacoes": ["Regras segregadas por CRT e CSTs/CSOSNs expandidos para maior flexibilidade fiscal."]
        }
        
        # --- REGIME NORMAL (CRT 3) ---
        new_rules["REGIME_NORMAL"] = {
            "icms": {
                "esperado": rules.get("icms", {}).get("esperado", False),
                "cst_validos": icms_cst
            },
            "ipi": {
                "esperado": rules.get("ipi", {}).get("esperado", False),
                "cst_validos": ipi_cst
            },
            "pis_cofins": {
                "credito": is_entrada, # True para entrada, False para saída
                "cst_validos": pis_cofins_cst
            }
        }
        
        # --- SIMPLES NACIONAL (CRT 1 ou 2) ---
        new_rules["SIMPLES_NACIONAL"] = {
            "icms": {
                "esperado": rules.get("icms", {}).get("esperado", False),
                "csosn_validos": ICMS_CSOSN_VALIDOS # CSOSN é padrão para Simples Nacional
            },
            "ipi": {
                "esperado": rules.get("ipi", {}).get("esperado", False),
                "cst_validos": ["53", "55", "99"] # IPI no Simples Nacional costuma ser isento/outras
            },
            "pis_cofins": {
                "credito": is_entrada,
                # Simples Nacional utiliza CSTs PIS/COFINS limitados ou padrões. Usaremos a lista flexível de saída como base.
                "cst_validos": PIS_COFINS_CST_SAIDA if is_saida else PIS_COFINS_CST_ENTRADA
            }
        }
        
        optimized_data["per_cfop"][cfop] = new_rules

    # Manter a seção per_group se existir, ou criar uma base
    optimized_data["per_group"] = data.get("per_group", {
        "1": {"tipo_operacao": "entrada", "icms": {"esperado": True}, "ipi": {"esperado": False}, "pis_cofins": {"credito": True}},
        "5": {"tipo_operacao": "saida", "icms": {"esperado": True}, "ipi": {"esperado": False}, "pis_cofins": {"credito": False}}
    })

    return optimized_data

# --- 3. Execução e Salvamento ---

INPUT_FILE = "cfop_rules_generated.json"
OUTPUT_FILE = "cfop_rules_optimized.json"

try:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"Lendo dados de: {INPUT_FILE}")

    optimized_rules = optimize_cfop_rules(original_data)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(optimized_rules, f, indent=2, ensure_ascii=False)
        
    print(f"Sucesso! Arquivo otimizado salvo como: {OUTPUT_FILE}")
    print("\nVerifique a nova estrutura com a segregação por REGIME_NORMAL e SIMPLES_NACIONAL.")

except FileNotFoundError:
    print(f"Erro: O arquivo de entrada '{INPUT_FILE}' não foi encontrado. Verifique se ele está no mesmo diretório do script.")
except json.JSONDecodeError:
    print(f"Erro: O arquivo '{INPUT_FILE}' não é um JSON válido. Verifique a sintaxe.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")

# --- 4. Exemplo de Como Fica o CFOP 5102 ---
# (Apenas para demonstração de como a estrutura é gerada)

if '5102' in optimized_rules["per_cfop"]:
    print("\n--- Exemplo de CFOP 5102 Otimizado ---")
    print(json.dumps(optimized_rules["per_cfop"]["5102"], indent=2, ensure_ascii=False))