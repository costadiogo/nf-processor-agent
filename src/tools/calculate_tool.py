import json

from langchain_core.tools import tool
from src.database.connection import get_connection

@tool
def calcular_totais() -> str:
    """
    Calcula totais de valores e impostos de todas as notas.
    
    Returns:
        JSON com totais calculados
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Total de notas e valores
        cursor.execute("""
            SELECT 
                COUNT(*) as total_notas,
                SUM(valor_total) as valor_total,
                COUNT(CASE WHEN classificacao = 'Produto' THEN 1 END) as total_produtos,
                COUNT(CASE WHEN classificacao = 'Serviço' THEN 1 END) as total_servicos
            FROM notas_fiscais
        """)
        
        totais = dict(cursor.fetchone())
        
        # Impostos por tipo
        cursor.execute("""
            SELECT 
                tipo_imposto,
                SUM(valor_imposto) as total_imposto
            FROM impostos
            GROUP BY tipo_imposto
        """)
        
        impostos = [dict(row) for row in cursor.fetchall()]
        totais['impostos'] = impostos
        
        conn.close()
        
        return json.dumps(totais, ensure_ascii=False, default=str)
        
    except Exception as e:
        return f"❌ Erro ao calcular totais: {str(e)}"