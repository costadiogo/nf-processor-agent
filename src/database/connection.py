"""Gerenciamento de conexão SQLite."""

import sqlite3
from pathlib import Path
from typing import Optional

from config.configuration import DATABASE_PATH, DATABASE_TIMEOUT
from logs.logger import app_logger


def get_connection() -> sqlite3.Connection:
    """Retorna conexão com banco de dados."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=DATABASE_TIMEOUT)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Inicializa banco de dados e cria tabelas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de notas fiscais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_nf TEXT NOT NULL,
            serie TEXT NOT NULL,
            tipo_nf TEXT NOT NULL,
            data_emissao TIMESTAMP NOT NULL,
            data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            classificacao TEXT NOT NULL,
            cfop TEXT NULL,
            natop TEXT NULL,
            sct TEXT NULL,
            valor_total REAL NULL,
            fornecedor_cnpj TEXT NULL,
            cliente_cnpj TEXT NULL,
            cliente_cpf TEXT NULL,
            status TEXT DEFAULT 'Pendente',
            justificativa TEXT,
            chave_nfe TEXT UNIQUE,
            protocolo_sefaz TEXT,
            mensagem_erro TEXT,
            data_autorizacao TIMESTAMP,
            UNIQUE(numero_nf, serie)
        )
    """)
    
    # Tabela de itens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nf_id INTEGER NOT NULL,
            codigo_item TEXT NOT NULL,
            descricao TEXT NOT NULL,
            quantidade REAL NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            tipo TEXT NOT NULL,
            ncm TEXT,
            FOREIGN KEY (nf_id) REFERENCES notas_fiscais(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de impostos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS impostos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nf_id INTEGER NOT NULL,
            tipo_imposto TEXT NOT NULL,
            aliquota REAL NOT NULL,
            valor_base REAL NOT NULL,
            valor_imposto REAL NOT NULL,
            FOREIGN KEY (nf_id) REFERENCES notas_fiscais(id) ON DELETE CASCADE
        )
    """)
    
    # Índices para performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_numero ON notas_fiscais(numero_nf)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_data ON notas_fiscais(data_emissao)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_status ON notas_fiscais(status)")
    
    conn.commit()
    conn.close()
    
    app_logger.info(f"✅ Banco de dados inicializado em {DATABASE_PATH}")


def insert_nota_fiscal(nf_data: dict, cursor) -> int:
    """Insere ou atualiza nota fiscal usando cursor existente e retorna ID."""
    
    # Colunas a serem inseridas/atualizadas
    cols = (
        'numero_nf', 'serie', 'tipo_nf', 'data_emissao', 'classificacao', 'cfop', 'natop', 'sct',
        'valor_total', 'fornecedor_cnpj', 'cliente_cnpj', 'cliente_cpf', 'status', 'justificativa',
        'chave_nfe', 'protocolo_sefaz', 'data_autorizacao', 'mensagem_erro'
    )
    
    update_fields = [
        f"{col}=EXCLUDED.{col}" 
        for col in cols if col not in ['numero_nf', 'serie'] # Não atualiza a chave
    ]
    update_clause = ", ".join(update_fields)
    
    placeholders = ", ".join(["?"] * len(cols))

    sql = f"""
        INSERT INTO notas_fiscais ({", ".join(cols)})
        VALUES ({placeholders})
        ON CONFLICT (numero_nf, serie) DO UPDATE SET
            {update_clause}
    """

    values = (
        nf_data['numero_nf'], nf_data['serie'], nf_data['tipo_nf'], nf_data['data_emissao'], 
        nf_data['classificacao'], nf_data['cfop'], nf_data['natop'], nf_data['sct'],
        nf_data['valor_total'], nf_data['fornecedor_cnpj'], nf_data['cliente_cnpj'], 
        nf_data['cliente_cpf'], nf_data.get('status', 'Pendente'), nf_data.get('justificativa'),
        nf_data.get('chave_nfe'), nf_data.get('protocolo_sefaz'), nf_data.get('data_autorizacao'),
        nf_data.get('mensagem_erro')
    )

    cursor.execute(sql, values)
    
    cursor.execute(
        "SELECT id FROM notas_fiscais WHERE numero_nf = ? AND serie = ?",
        (nf_data['numero_nf'], nf_data['serie'])
    )
    nf_id = cursor.fetchone()[0]
    
    return nf_id


def get_all_notas() -> list[dict]:
    """Retorna todas as notas fiscais."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notas_fiscais ORDER BY data_emissao DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_nota_by_id(nf_id: int) -> Optional[dict]:
    """Retorna nota fiscal por ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notas_fiscais WHERE id = ?", (nf_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None
