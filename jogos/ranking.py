import sqlite3
from database import conectar_banco

def calcular_placar_e_ranking(id_rodada: int, numeros_sorteados: list) -> dict:
    """
    Busca todos os jogos ativos da rodada, cruza com os números oficiais
    e devolve o ranking organizado com os ganhadores e os amarrados.
    """
    # Transforma o resultado da Caixa em um conjunto matemático para cruzamento rápido
    dezenas_oficiais = set(numeros_sorteados)
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    try:
        # Busca apenas os jogos que estão correndo (Ativos) nesta rodada específica
        cursor.execute("""
            SELECT j.id, j.cpf_usuario, j.dezenas, u.nome 
            FROM jogos j
            JOIN usuarios u ON j.cpf_usuario = u.cpf
            WHERE j.id_rodada = ? AND j.status = 'Ativo'
        """, (id_rodada,))
        
        todos_os_bilhetes = cursor.fetchall()
        
        ranking_geral = []
        ganhadores_principais = []
        amarrados_na_trave = []  # Quem acertou exatamente 5 números

        for bilhete in todos_os_bilhetes:
            # Transforma a string '02,15,34...' em uma lista de números inteiros [2, 15, 34...]
            dezenas_usuario = [int(n) for n in bilhete["dezenas"].split(",")]
            
            # Cruza os dois conjuntos para descobrir quais números batem (Interseção)
            acertos = set(dezenas_usuario).intersection(dezenas_oficiais)
            total_acertos = len(acertos)
            
            dados_jogador = {
                "id_bilhete": bilhete["id"],
                "nome": bilhete["nome"],
                "cpf": bilhete["cpf_usuario"],
                "dezenas_jogadas": dezenas_usuario,
                "numeros_acertados": list(acertos),
                "total_acertos": total_acertos
            }
            
            ranking_geral.append(dados_jogador)
            
            # Separa os casos especiais de vitória
            if total_acertos == 6:
                ganhadores_principais.append(dados_jogador)
            elif total_acertos == 5:
                amarrados_na_trave.append(dados_jogador)
                
        # Organiza a lista do ranking jogando quem tem mais acertos para o topo da tabela
        ranking_ordenado = sorted(ranking_geral, key=lambda x: x["total_acertos"], reverse=True)
        
        return {
            "sucesso": True,
            "ranking": ranking_ordenado,
            "houve_ganhador_maximo": len(ganhadores_principais) > 0,
            "ganhadores": ganhadores_principais,
            "amarrados_5_acertos": amarrados_na_trave
        }
        
    except Exception as e:
        return {"sucesso": False, "erro": f"Erro ao processar ranking: {str(e)}"}
    finally:
        conexao.close()
