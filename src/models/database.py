import sqlite3

DATABASE_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    with get_db_connection() as conn:
        # 1. Tabela de Usuários
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nome TEXT, 
                email TEXT UNIQUE, 
                senha TEXT, 
                perfil TEXT
            )
        """)
        
        # 2. Tabelas do Caixa e Vendas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS caixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                op TEXT, 
                status TEXT, 
                ini REAL, 
                fin REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                valor REAL, 
                m_pago TEXT
            )
        """)
        
        # 3. Tabela de Ocupação da Portaria
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ocupacao (
                cartao_id TEXT PRIMARY KEY, 
                status TEXT, 
                entrado_em TEXT
            )
        """)
        
        # 4. Tabela de Gerenciamento da Fila
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gerenciamento_fila (
                senha INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                status TEXT CHECK(status IN ('esperando', 'chamado', 'dentro', 'saiu', 'cancelado')) DEFAULT 'esperando',
                horario_gerado TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        
        # 5. Tabela de Produtos / Estoque
        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                quantidade INTEGER NOT NULL,
                estoque_minimo INTEGER DEFAULT 5
            )
        """)