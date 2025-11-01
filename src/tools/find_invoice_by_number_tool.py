import json

from langchain_core.tools import tool
from src.database.connection import get_connection

@tool
def buscar_nota_por_numero(numero_nf: str) -> str:
    """
    Busca uma nota fiscal pelo número.
    
    Args:
        numero_nf: Número da nota fiscal
    
    Returns:
        JSON com dados da nota ou mensagem de erro
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM notas_fiscais 
            WHERE numero_nf = ?
        """, (numero_nf,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return f"❌ Nota fiscal {numero_nf} não encontrada no banco de dados."
        
        nf = dict(row)
        return json.dumps(nf, ensure_ascii=False, default=str)
        
    except Exception as e:
        return f"❌ Erro ao buscar nota: {str(e)}"