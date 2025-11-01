import json

from langchain_core.tools import tool
from src.database.connection import get_connection

@tool
def listar_notas_recentes(limite: int = 10) -> str:
    """
    Lista as notas fiscais mais recentes.
    
    Args:
        limite: Número máximo de notas a retornar
    
    Returns:
        JSON com lista de notas
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT numero_nf, serie, data_emissao, valor_total, status, classificacao
            FROM notas_fiscais 
            ORDER BY data_processamento DESC
            LIMIT ?
        """, (limite,))
        
        rows = cursor.fetchall()
        conn.close()
        
        notas = [dict(row) for row in rows]
        return json.dumps(notas, ensure_ascii=False, default=str)
        
    except Exception as e:
        return f"❌ Erro ao listar notas: {str(e)}"