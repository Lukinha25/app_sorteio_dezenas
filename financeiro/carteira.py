import sqlite3
from database import conectar_banco

def consultar_saldo(cpf_usuario: str) -> dict:
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT saldo FROM carteiras WHERE cpf_usuario = ?", (cpf_usuario,))
        resultado = cursor.fetchone()
        if resultado:
            return {"sucesso": True, "saldo": resultado["saldo"]}
        return {"sucesso": False, "erro": "Carteira não encontrada."}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()

def adicionar_saldo_com_bonus(cpf_usuario: str, valor_deposito: float) -> dict:
    valor_final = valor_deposito
    ganhou_bonus = False
    
    if valor_deposito >= 20.0:
        valor_final += 10.0
        ganhou_bonus = True
        
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE carteiras SET saldo = saldo + ? WHERE cpf_usuario = ?", (valor_final, cpf_usuario))
        
        # Grava a entrada na tabela de histórico
        cursor.execute("INSERT INTO historico (cpf_usuario, tipo, valor) VALUES (?, 'Deposito', ?)", (cpf_usuario, valor_final))
        
        conexao.commit()
        msg = f"Saldo de R$ {valor_deposito:.2f} adicionado!"
        if ganhou_bonus:
            msg += " 🎁 Ganhado +R$ 10,00 de Bônus!"
        return {"sucesso": True, "mensagem": msg}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()

def debitar_custo_bilhete(cpf_usuario: str, custo: float = 10.0) -> dict:
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT saldo FROM carteiras WHERE cpf_usuario = ?", (cpf_usuario,))
        resultado = cursor.fetchone()
        if not resultado or resultado["saldo"] < custo:
            return {"sucesso": False, "erro": "Saldo insuficiente."}
            
        cursor.execute("UPDATE carteiras SET saldo = saldo - ? WHERE cpf_usuario = ?", (custo, cpf_usuario))
        cursor.execute("INSERT INTO historico (cpf_usuario, tipo, valor) VALUES (?, 'Compra Bilhete', ?)", (cpf_usuario, custo))
        
        conexao.commit()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()
