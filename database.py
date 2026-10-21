import sqlite3

DATABASE_NAME = "sistema_sorteios.db"

def conectar_banco():
    conexao = sqlite3.connect(DATABASE_NAME)
    conexao.row_factory = sqlite3.Row
    return conexao

def inicializar_tabelas():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    # 1. Tabela de Usuários (Com e-mail, foto e código de convite)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        cpf TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        senha_cripto TEXT NOT NULL,
        codigo_convite TEXT UNIQUE NOT NULL,
        indicado_por TEXT,
        email TEXT DEFAULT '',
        foto_url TEXT DEFAULT '/static/imagens/avatar_padrao.png'
    )
    """)
    
    # 2. Tabela de Carteiras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carteiras (
        cpf_usuario TEXT PRIMARY KEY,
        saldo REAL DEFAULT 0.0
    )
    """)
    
    # 3. Tabela de Jogos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jogos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_usuario TEXT NOT NULL,
        dezenas TEXT NOT NULL,
        id_rodada INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Ativo'
    )
    """)

    # 4. Tabela de Histórico Financeiro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_usuario TEXT NOT NULL,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Tabela de Mural de Avisos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mural (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_usuario TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conexao.commit()
    conexao.close()
    print("🔋 Banco de dados e tabelas reiniciados com sucesso!")

if __name__ == "__main__":
    inicializar_tabelas()
