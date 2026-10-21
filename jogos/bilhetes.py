import sqlite3
from database import conectar_banco
from financeiro.carteira import debitar_custo_bilhete

def registrar_aposta(cpf_usuario: str, dezenas_escolhidas: list, id_rodada: int) -> dict:
    """Valida as dezenas, cobra os R$ 10 do saldo e grava o bilhete no banco."""
    if len(dezenas_escolhidas) != 6:
        return {"sucesso": False, "erro": "Você precisa selecionar exatamente 6 números!"}
        
    # 1. Tenta cobrar os R$ 10 da carteira do usuário
    cobranca = debitar_custo_bilhete(cpf_usuario, custo=10.0)
    if not cobranca["sucesso"]:
        return {"sucesso": False, "erro": cobranca["erro"]}
        
    # 2. Se o pagamento deu certo, prepara e salva as dezenas
    dezenas_limpas = sorted([int(n) for n in dezenas_escolhidas])
    dezenas_texto = ",".join(f"{n:02d}" for n in dezenas_limpas)
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO jogos (cpf_usuario, dezenas, id_rodada, status)
            VALUES (?, ?, ?, 'Ativo')
        """, (cpf_usuario, dezenas_texto, id_rodada))
        conexao.commit()
        return {"sucesso": True, "mensagem": "Bilhete registrado com sucesso! Boa sorte!"}
    except Exception as e:
        return {"sucesso": False, "erro": f"Erro ao salvar jogo: {str(e)}"}
    finally:
        conexao.close()


def buscar_historico_bilhetes(cpf_usuario: str) -> list:
    """Busca todos os bilhetes (Ativos ou Finalizados) do usuário no banco."""
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT id, dezenas, id_rodada, status 
            FROM jogos 
            WHERE cpf_usuario = ? 
            ORDER BY id DESC
        """, (cpf_usuario,))
        bilhetes = cursor.fetchall()
        return [{
            "id": b["id"],
            "dezenas": b["dezenas"],
            "id_rodada": b["id_rodada"],
            "status": b["status"]
        } for b in bilhetes]
    except Exception:
        return []
    finally:
        conexao.close()
