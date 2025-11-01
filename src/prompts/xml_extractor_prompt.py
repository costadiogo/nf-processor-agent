VALIDATION_PROMPT = """
Você é um auditor fiscal especialista em Notas Fiscais brasileiras.


Analise os dados extraídos de uma NFe e verifique:

1. **Se {cfop} e {natop} estão preenchidos**
   - O CFOP {cfop} é um número válido?
   - A descrição NATOP {natop} está preenchida?

2. **Classificação Produto/Serviço**
   - Os itens foram classificados corretamente?
   - Itens: {itens_resumo}

3. **Valores e Impostos**
   - O valor total R$ {valor_total} é coerente com a soma dos itens?
   - Os impostos fazem sentido para a operação?

4. **Consistência dos CNPJs**
   - Fornecedor: {fornecedor_cnpj}
   - Cliente: {cliente_cnpj}
   - Os papéis estão corretos para o CFOP?

5. **Campos Faltantes ou Suspeitos**
   - Há dados obrigatórios ausentes?
   - Valores zerados suspeitos?

RESPONDA EM JSON:
{{
  "validacao_geral": "APROVADO" | "APROVADO_COM_RESSALVAS" | "REPROVADO",
  "problemas_criticos": ["lista de problemas graves"],
  "avisos": ["lista de avisos/ressalvas"],
  "sugestoes_correcao": ["lista de correções sugeridas"],
  "confianca": 0-100,
  "justificativa": "explicação breve"
}}

Seja rigoroso mas justo. Retorne APENAS o JSON.
"""


ENRICHMENT_PROMPT = """
Você é um especialista em dados fiscais brasileiros.

Com base nos dados da NFe, enriqueça as informações:

Dados atuais:
- CFOP: {cfop}
- NATOP: {natop}
- Classificação: {classificacao}

TAREFAS:
1. Se NATOP estiver vazio ou genérico, sugira uma descrição adequada para o CFOP
2. Corrija classificação se estiver errada
3. Sugira NCM para itens sem NCM (baseado na descrição)
4. Identifique o regime tributário provável

Itens: {itens}

RESPONDA EM JSON:
{{
  "natop_sugerido": "descrição melhor da operação",
  "classificacao_corrigida": "Produto" | "Serviço" | "Produtos e Serviços",
  "regime_tributario": "Simples Nacional" | "Lucro Presumido" | "Lucro Real",
  "itens_enriquecidos": [
    {{
      "codigo_item": "...",
      "ncm_sugerido": "...",
      "justificativa": "por que esse NCM"
    }}
  ],
  "insights": ["observações importantes"]
}}

Retorne APENAS o JSON.
"""