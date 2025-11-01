"""Prompts para validação fiscal rigorosa com LLM."""

FISCAL_VALIDATION_PROMPT = """
Você é um AUDITOR FISCAL ESPECIALISTA em NFe (Nota Fiscal Eletrônica) brasileira.

Sua missão é VALIDAR RIGOROSAMENTE **TODOS OS ITENS** da nota fiscal para EVITAR MULTAS da SEFAZ.

🎯 OBJETIVO: Identificar TODOS os erros que causariam rejeição ou multa no ambiente de PRODUÇÃO.

⚠️ **REGRA CRÍTICA**: Se **QUALQUER ITEM** tiver erro, a nota INTEIRA deve ser REPROVADA.

📋 DADOS DA NFe PARA VALIDAR:

**IDENTIFICAÇÃO:**
- Número NF: {numero_nf}
- Série: {serie}
- Data Emissão: {data_emissao}
- CFOP: {cfop}
- Natureza Operação: {natop}

**EMITENTE:**
- CNPJ: {fornecedor_cnpj}
- UF: {uf_emitente}

**DESTINATÁRIO:**
- CNPJ: {cliente_cnpj}
- UF: {uf_destinatario}
- CPF: {cliente_cpf}

**ITENS (VALIDAR CADA UM INDIVIDUALMENTE):**
{itens_detalhados}

**IMPOSTOS TOTAIS:**
{impostos_totais}

---


**NÃO APROVAR NOTA COM "1 item errado e 9 certos"** - Se um erro = nota toda REPROVADA!
**VOCÊ DEVE VALIDAR SOMENTE SE OS CAMPOS NÃO ESTÃO VAZIOS**

---

## 📊 RESPONDA EM JSON:

{{
  "validacao_geral": "APROVADO" | "APROVADO_COM_RESSALVAS" | "REPROVADO",
  "score_confianca": 0-100,
  
  "validacao_por_item": [
    {{
      "numero_item": 1,
      "codigo_item": "...",
      "descricao": "...",
      "status": "OK" | "ERRO" | "AVISO",
      "erros": ["lista de erros deste item específico"],
      "campos_validados": {{
        "cfop_ok": true/false,
        "cst_ok": true/false,
        "ncm_ok": true/false,
        "valores_ok": true/false,
        "impostos_ok": true/false
      }}
    }}
  ],
  
  "erros_criticos": [
    {{
      "item": "número do item com erro (ou 'GERAL')",
      "campo": "CFOP/CST/NCM/etc",
      "erro": "descrição detalhada",
      "valor_encontrado": "valor incorreto",
      "valor_esperado": "como deveria ser",
      "impacto": "multa/rejeição automática/inconsistência",
      "sugestao_correcao": "como corrigir"
    }}
  ],
  
  "avisos": [
    {{
      "item": "número do item (ou 'GERAL')",
      "campo": "nome do campo",
      "aviso": "descrição",
      "risco": "baixo/médio/alto"
    }}
  ],
  
  "resumo_itens": {{
    "total_itens": 0,
    "itens_ok": 0,
    "itens_com_erro": 0,
    "itens_com_aviso": 0
  }},
  
  "resumo_fiscal": {{
    "cfop_ok": true/false,
    "cst_ok": true/false,
    "ncm_ok": true/false,
    "icms_ok": true/false,
    "ipi_ok": true/false,
    "pis_cofins_ok": true/false,
    "totalizadores_ok": true/false
  }},
  
  "recomendacao_sefaz": "APTO PARA PRODUÇÃO" | "CORRIGIR ANTES DE ENVIAR" | "REJEITADO - NÃO ENVIAR",
  
  "justificativa": "explicação detalhada incluindo quantos itens têm erro"
}}

⚠️ **IMPORTANTE:**
- Valide **ITEM POR ITEM** - não generalizar
- Um único item com erro = nota toda REPROVADA
- Seja RIGOROSO: CFOP "510" = ERRO (faltam dígitos)
- Liste TODOS os erros encontrados em TODOS os itens
- Score de confiança baseado na certeza da análise

Retorne APENAS o JSON, sem explicações adicionais.
"""


def format_fiscal_validation_prompt(nf_data: dict) -> str:
    """
    Formata o prompt de validação fiscal com os dados da NFe.
    
    Args:
        nf_data: Dicionário com dados da nota fiscal
    
    Returns:
        Prompt formatado
    """
    # Formatar itens detalhados
    itens_detalhados = []
    for idx, item in enumerate(nf_data.get('itens', []), 1):
        item_str = f"""
Item {idx}:
  - Código: {item.get('codigo_item', 'N/A')}
  - Descrição: {item.get('descricao', 'N/A')}
  - NCM: {item.get('ncm', 'N/A')}
  - CFOP: {item.get('cfop', 'N/A')}
  - Quantidade: {item.get('quantidade', 0)}
  - Valor Unitário: R$ {item.get('valor_unitario', 0):.2f}
  - Valor Total: R$ {item.get('valor_total', 0):.2f}
  - CST ICMS: {item.get('cst_icms', 'N/A')}
  - Alíquota ICMS: {item.get('aliq_icms', 0)}%
  - Valor ICMS: R$ {item.get('valor_icms', 0):.2f}
  - CST IPI: {item.get('cst_ipi', 'N/A')}
  - Alíquota IPI: {item.get('aliq_ipi', 0)}%
  - Valor IPI: R$ {item.get('valor_ipi', 0):.2f}
  - CST PIS: {item.get('cst_pis', 'N/A')}
  - Alíquota PIS: {item.get('aliq_pis', 0)}%
  - Valor PIS: R$ {item.get('valor_pis', 0):.2f}
  - CST COFINS: {item.get('cst_cofins', 'N/A')}
  - Alíquota COFINS: {item.get('aliq_cofins', 0)}%
  - Valor COFINS: R$ {item.get('valor_cofins', 0):.2f}
"""
        itens_detalhados.append(item_str)
    
    itens_text = "\n".join(itens_detalhados) if itens_detalhados else "Nenhum item encontrado"
    
    # Formatar impostos totais
    impostos_totais = []
    for imposto in nf_data.get('impostos', []):
        impostos_totais.append(
            f"  - {imposto.get('tipo_imposto', 'N/A')}: "
            f"R$ {imposto.get('valor_imposto', 0):.2f} "
            f"({imposto.get('aliquota', 0)}%)"
        )
    
    impostos_text = "\n".join(impostos_totais) if impostos_totais else "Nenhum imposto calculado"
    
    # Formatar prompt
    return FISCAL_VALIDATION_PROMPT.format(
        numero_nf=nf_data.get('numero_nf', 'N/A'),
        serie=nf_data.get('serie', 'N/A'),
        data_emissao=nf_data.get('data_emissao', 'N/A'),
        cfop=nf_data.get('cfop', 'N/A'),
        natop=nf_data.get('natop', 'N/A'),
        fornecedor_cnpj=nf_data.get('fornecedor_cnpj', 'N/A'),
        uf_emitente=nf_data.get('uf_emitente', 'N/A'),
        cliente_cnpj=nf_data.get('cliente_cnpj', 'N/A'),
        cliente_cpf=nf_data.get('cliente_cpf', 'N/A'),
        uf_destinatario=nf_data.get('uf_destinatario', 'N/A'),
        itens_detalhados=itens_text,
        impostos_totais=impostos_text
    )