import sqlite3
from database import conectar_banco

def enviar_mensagem_mural(cpf_usuario: str, mensagem: str) -> dict:
    """Grava um novo comentário da galera no banco de dados."""
    if not mensagem.strip():
        return {"sucesso": False, "erro": "A mensagem não pode estar vazia."}
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO mural (cpf_usuario, mensagem) VALUES (?, ?)", (cpf_usuario, mensagem))
        conexao.commit()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()

def listar_mensagens_mural() -> list:
    """Busca as últimas 20 mensagens enviadas no mural para exibir na tela."""
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT m.mensagem, m.data_hora, u.nome 
            FROM mural m
            JOIN usuarios u ON m.cpf_usuario = u.cpf
            ORDER BY m.id DESC LIMIT 20
        """)
        mensagens = cursor.fetchall()
        return [{
            "nome": msg["nome"],
            "mensagem": msg["mensagem"],
            "data": msg["data_hora"]
        } for msg in mensagens]
    except Exception:
        return []
    finally:
        conexao.close()
