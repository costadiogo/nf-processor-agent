import json

from langchain_core.tools import tool
from src.database.connection import get_connection

@tool
def estatisticas_gerais() -> str:
    """
    Gera estatísticas gerais sobre as notas processadas.
    
    Returns:
        JSON com estatísticas
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de notas por status
        cursor.execute("""
            SELECT status, COUNT(*) as quantidade
            FROM notas_fiscais
            GROUP BY status
        """)
        stats['por_status'] = [dict(row) for row in cursor.fetchall()]
        
        # Total de notas por tipo
        cursor.execute("""
            SELECT tipo_nf, COUNT(*) as quantidade
            FROM notas_fiscais
            GROUP BY tipo_nf
        """)
        stats['por_tipo'] = [dict(row) for row in cursor.fetchall()]
        
        # Média de valor por classificação
        cursor.execute("""
            SELECT 
                classificacao,
                AVG(valor_total) as valor_medio,
                MIN(valor_total) as valor_minimo,
                MAX(valor_total) as valor_maximo
            FROM notas_fiscais
            GROUP BY classificacao
        """)
        stats['valores'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        print("✅ Estatísticas geradas com sucesso", stats)
        return json.dumps(stats, ensure_ascii=False, default=str)
        
    except Exception as e:
        return f"❌ Erro ao gerar estatísticas: {str(e)}"