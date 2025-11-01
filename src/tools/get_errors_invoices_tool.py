import json

from langchain_core.tools import tool
from src.database.connection import get_connection

@tool
def buscar_notas_com_erro() -> str:
    """
    Lista notas fiscais com erros de validação.
    
    Returns:
        JSON com lista de notas com erro
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT numero_nf, serie, status, mensagem_erro, data_emissao
            FROM notas_fiscais 
            WHERE status = 'Reprovado'
            ORDER BY data_processamento DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        notas = [dict(row) for row in rows]
        return json.dumps(notas, ensure_ascii=False, default=str)
        
    except Exception as e:
        return f"❌ Erro ao buscar notas com erro: {str(e)}"