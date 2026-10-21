import sqlite3
import secrets
import string
from database import conectar_banco

def validar_cpf(cpf: str) -> bool:
    """Retorna True temporariamente para facilitar os testes locais no PC."""
    return True

def gerar_codigo_convite(nome: str) -> str:
    letras = "".join(c for c in nome if c.isalpha()).upper()[:4]
    numeros = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"{letras}{numeros}"

def cadastrar_novo_usuario(cpf: str, nome: str, senha_pura: str, codigo_padrinho: str = None) -> dict:
    cpf_limpo = "".join(c for c in cpf if c.isdigit())
    if not cpf_limpo:
        return {"sucesso": False, "erro": "CPF vazio."}

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT cpf FROM usuarios WHERE cpf = ?", (cpf_limpo,))
        if cursor.fetchone():
            return {"sucesso": False, "erro": "Este CPF já possui uma conta cadastrada."}
            
        cpf_padrinho = None
        if codigo_padrinho:
            cursor.execute("SELECT cpf FROM usuarios WHERE codigo_convite = ?", (codigo_padrinho.upper(),))
            padrinho = cursor.fetchone()
            if padrinho:
                cpf_padrinho = padrinho["cpf"]
        
        novo_codigo_afiliado = gerar_codigo_convite(nome)

        cursor.execute("""
            INSERT INTO usuarios (cpf, nome, senha_cripto, codigo_convite, indicado_por)
            VALUES (?, ?, ?, ?, ?)
        """, (cpf_limpo, nome, senha_pura, novo_codigo_afiliado, cpf_padrinho))
        
        cursor.execute("INSERT INTO carteiras (cpf_usuario, saldo) VALUES (?, 0.0)", (cpf_limpo,))
        
        conexao.commit()
        return {
            "sucesso": True, 
            "mensagem": "Conta criada com sucesso!",
            "seu_codigo_afiliado": novo_codigo_afiliado
        }
    except Exception as e:
        conexao.rollback()
        return {"sucesso": False, "erro": f"Erro de banco: {str(e)}"}
    finally:
        conexao.close()

def obter_dados_perfil_completo(cpf: str) -> dict:
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT nome, email, foto_url, codigo_convite FROM usuarios WHERE cpf = ?", (cpf,))
        usuario = cursor.fetchone()
        if not usuario:
            return {"sucesso": False, "erro": "Usuário não encontrado."}

        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE indicado_por = ?", (cpf,))
        total_indicados = cursor.fetchone()["total"]

        cursor.execute("SELECT tipo, valor, data_hora FROM historico WHERE cpf_usuario = ? ORDER BY id DESC", (cpf,))
        movimentacoes = cursor.fetchall()
        
        lista_historico = []
        for mov in movimentacoes:
            lista_historico.append({
                "tipo": mov["tipo"],
                "valor": mov["valor"],
                "data": mov["data_hora"]
            })

        return {
            "sucesso": True,
            "nome": usuario["nome"],
            "email": usuario["email"],
            "foto_url": usuario["foto_url"],
            "codigo_convite": usuario["codigo_convite"],
            "total_indicados": total_indicados,
            "historico": lista_historico
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()

def atualizar_dados_cadastro(cpf: str, email: str, foto_url: str) -> dict:
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE usuarios SET email = ?, foto_url = ? WHERE cpf = ?", (email, foto_url, cpf))
        conexao.commit()
        return {"sucesso": True, "mensagem": "Perfil atualizado com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
    finally:
        conexao.close()
