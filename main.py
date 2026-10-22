from database import conectar_banco, inicializar_tabelas
from financeiro.pix_inter import gerar_qrcode_pix_inter_real
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from jogos.bilhetes import registrar_aposta, buscar_historico_bilhetes
from jogos.bilhetes import buscar_historico_bilhetes
from jogos.mural import enviar_mensagem_mural, listar_mensagens_mural
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from usuarios.gerenciar import cadastrar_novo_usuario, obter_dados_perfil_completo, atualizar_dados_cadastro
from jogos.bilhetes import registrar_aposta
from jogos.api_caixa import buscar_resultado_caixa
from jogos.ranking import calcular_placar_e_ranking
from financeiro.carteira import consultar_saldo, adicionar_saldo_com_bonus

app = FastAPI(title="App de Sorteio de Dezenas")

# Configuração obrigatória das pastas visuais do sistema web
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Liga o motor do banco de dados ao iniciar o servidor
inicializar_tabelas()


# =========================================================================
# 📱 1. ROTAS VISUAIS (FRONT-END) - ABREM AS TELAS NO NAVEGADOR
# =========================================================================
# ADICIONE ESSAS DUAS ROTAS ABAIXO DA ROTA DO VOLANTE NO SEU MAIN.PY
@app.get("/cadastro", response_class=HTMLResponse)
def abrir_pagina_cadastro(request: Request):
    """Renderiza a página HTML de criação de conta."""
    return templates.TemplateResponse(request=request, name="cadastro.html")

@app.get("/login", response_class=HTMLResponse)
def abrir_pagina_login(request: Request):
    """Renderiza a página HTML de login de acesso."""
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/", response_class=HTMLResponse)
def abrir_painel_jogos(request: Request):
    """Abre a tela principal do volante de 60 dezenas."""
    return templates.TemplateResponse(request=request, name="painel_jogos.html")

@app.get("/ranking", response_class=HTMLResponse)
def abrir_pagina_ranking(request: Request):
    """Abre a tela com a tabela de classificação e acertos ao vivo."""
    return templates.TemplateResponse(request=request, name="ranking.html")

@app.get("/carteira", response_class=HTMLResponse)
def abrir_pagina_carteira(request: Request):
    """Abre a tela da carteira digital para depósitos e saques."""
    return templates.TemplateResponse(request=request, name="carteira.html")
# COPIE E COLE ESSA ROTA LOGO ABAIXO DA ROTA DA CARTEIRA NO SEU MAIN.PY
@app.get("/perfil", response_class=HTMLResponse)
def abrir_pagina_perfil(request: Request):
    """Renderiza a página HTML do perfil do usuário e painel de afiliados."""
    return templates.TemplateResponse(request=request, name="perfil.html")
# COPIE E COLE ESSA ROTA LOGO ABAIXO DA ROTA DO PERFIL NO SEU MAIN.PY
@app.get("/tutorial", response_class=HTMLResponse)
def abrir_pagina_tutorial(request: Request):
    """Renderiza a página HTML do tutorial explicativo do jogo."""
    return templates.TemplateResponse(request=request, name="tutorial.html")




# =========================================================================
# ⚙️ 2. ROTAS LOGICAS (BACK-END / API) - FAZEM O MOTOR DO APP FUNCIONAR
# =========================================================================

class FormularioCadastro(BaseModel):
    cpf: str
    nome: str
    senha: str
    codigo_indizacao: str = None

class FormularioJogo(BaseModel):
    cpf: str
    dezenas: list
    id_rodada: int

class FormularioDeposito(BaseModel):
    cpf: str
    valor: float

@app.post("/api/usuarios/cadastrar")
def rota_cadastrar(dados: FormularioCadastro):
    resultado = cadastrar_novo_usuario(dados.cpf, dados.nome, dados.senha, dados.codigo_indizacao)
    if not resultado["sucesso"]: raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado
# COLE ESTE BLOCO EXATAMENTE LOGO ABAIXO DA ROTA DE CADASTRAR NO SEU MAIN.PY
class FormularioLogin(BaseModel):
    cpf: str
    senha: str

@app.post("/api/usuarios/login")
def rota_login_oficial(dados: FormularioLogin):
    """Verifica se o CPF e a Senha existem de verdade no banco de dados antes de liberar o acesso."""
    # Remove pontos e traços do CPF enviado pela tela
    cpf_limpo = "".join(c for c in dados.cpf if c.isdigit())
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # Busca o usuário cadastrado no arquivo de banco de dados (.db)
        cursor.execute("SELECT cpf, senha_cripto FROM usuarios WHERE cpf = ?", (cpf_limpo,))
        usuario = cursor.fetchone()
        
        # 🛡️ BARREIRA DE SEGURANÇA: Se o CPF não existir ou a senha estiver incorreta, bloqueia!
        if not usuario or usuario["senha_cripto"] != dados.senha:
            raise HTTPException(status_code=400, detail="CPF ou Senha incorretos! Crie uma conta se for novo.")
            
        return {"sucesso": True, "mensagem": "Login autorizado com sucesso! Bem-vindo ao app."}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno de banco: {str(e)}")
    finally:
        conexao.close()


@app.post("/api/jogos/comprar")
def rota_comprar_jogo(dados: FormularioJogo):
    resultado = registrar_aposta(dados.cpf, dados.dezenas, dados.id_rodada)
    if not resultado["sucesso"]: raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado

@app.get("/api/caixa/ultimo-sorteio")
def rota_ver_sorteio_caixa():
    resultado = buscar_resultado_caixa()
    if not resultado["sucesso"]: raise HTTPException(status_code=500, detail=resultado["erro"])
    return resultado

@app.get("/api/jogos/ranking/{id_rodada}")
def rota_ver_ranking(id_rodada: int):
    """
    Rota acionada pelo site para renderizar a tabela de classificação dos jogadores.
    Busca o resultado da Caixa e calcula o placar em tempo real.
    """
    # Aciona o nosso robô atualizado com o plano B de segurança contra erro 500
    resultado_caixa = buscar_resultado_caixa()
    if not resultado_caixa["sucesso"]:
        raise HTTPException(status_code=500, detail="Não foi possível obter o resultado da Caixa.")
        
    dezenas_oficiais = resultado_caixa["dezenas"]
    
    # Executa a nossa lógica matemática de cruzamento de apostas
    placar = calcular_placar_e_ranking(id_rodada, dezenas_oficiais)
    if not placar["sucesso"]:
        raise HTTPException(status_code=500, detail=placar["erro"])
        
    return placar


@app.get("/api/carteira/saldo/{cpf}")
def rota_ver_saldo(cpf: str):
    resultado = consultar_saldo(cpf)
    if not resultado["sucesso"]: raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado

@app.post("/api/carteira/depositar")
def rota_simular_deposito(dados: FormularioDeposito):
    """
    Aciona a API do Banco Inter para gerar o Pix Real do depósito, 
    e adiciona o dinheiro com bônus direto no banco de dados.
    """
    if dados.valor <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser maior que zero.")
        
    # Gera a cobrança do Pix utilizando o motor do Banco Inter
    dados_pix = gerar_qrcode_pix_inter_real(dados.valor, dados.cpf)
    if not dados_pix["sucesso"]:
        raise HTTPException(status_code=500, detail=dados_pix["erro"])
        
    # Executa a nossa gravação financeira no banco de dados do sistema
    resultado_saldo = adicionar_saldo_com_bonus(dados.cpf, dados.valor)
    if not resultado_saldo["sucesso"]:
        raise HTTPException(status_code=500, detail=resultado_saldo["erro"])
        
    # Retorna o QR Code e o Copia e Cola para a tela do site exibir ao cliente
    return {
        "sucesso": True,
        "mensagem": resultado_saldo["mensagem"],
        "pix_copia_cola": dados_pix["pix_copia_cola"],
        
        # AJUSTE AQUI: Mudamos para puxar o nome correto que está no pix_inter.py!
        "qrcode_url": dados_pix["qrcode_base64_url"] 
    }

@app.get("/api/usuarios/perfil/{cpf}")
def rota_obter_perfil(cpf: str):
    """API que busca os dados cadastrais, indicados e histórico do usuário."""
    resultado = obter_dados_perfil_completo(cpf)
    if not resultado["sucesso"]: 
        raise HTTPException(status_code=404, detail=resultado["erro"])
    return resultado

class FormularioAtualizarPerfil(BaseModel):
    cpf: str
    email: str
    foto_url: str

@app.post("/api/usuarios/perfil/atualizar")
def rota_atualizar_perfil(dados: FormularioAtualizarPerfil):
    """API que atualiza o e-mail e a foto no banco de dados."""
    resultado = atualizar_dados_cadastro(dados.cpf, dados.email, dados.foto_url)
    if not resultado["sucesso"]: 
        raise HTTPException(status_code=500, detail=resultado["erro"])
    return resultado

@app.get("/api/jogos/historico-bilhetes/{cpf}")
def rota_historico_bilhetes(cpf: str):
    """API que busca a lista de todos os jogos que o usuário comprou."""
    dados_bilhetes = buscar_historico_bilhetes(cpf)
    return {"sucesso": True, "bilhetes": dados_bilhetes}

@app.get("/api/mural/listar")
def rota_listar_mural():
    """API que lista os últimos comentários da rodada no ranking."""
    return {"sucesso": True, "mensagens": listar_mensagens_mural()}

class FormularioMural(BaseModel):
    cpf: str
    mensagem: str

@app.post("/api/mural/enviar")
def rota_enviar_mural(dados: FormularioMural):
    """API que grava um novo comentário enviado pelo usuário."""
    resultado = enviar_mensagem_mural(dados.cpf, dados.mensagem)
    if not resultado["sucesso"]: 
        raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado
import os

@app.post("/api/usuarios/perfil/upload-foto/{cpf}")
async def rota_upload_foto_perfil(cpf: str, file: UploadFile = File(...)):
    """Recebe a foto da galeria do celular e salva na pasta static/imagens."""
    # Garante que o arquivo enviado é realmente uma imagem
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado precisa ser uma imagem!")
        
    # Extrai a extensão do arquivo (ex: .png, .jpg)
    extensao = os.path.splitext(file.filename)[1].lower()
    if extensao not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")
        
    # Define o nome do arquivo usando o CPF para nunca duplicar (ex: 11310246645.png)
    nome_arquivo_salvo = f"{cpf}{extensao}"
    caminho_diretorio = "static/imagens"
    caminho_completo = os.path.join(caminho_diretorio, nome_arquivo_salvo)
    
    try:
        # Abre o arquivo local e grava os dados da imagem recebida
        with open(caminho_completo, "wb") as buffer:
            conteudo = await file.read()
            buffer.write(conteudo)
            
        # Atualiza o caminho da nova foto direto no banco de dados do usuário
        url_banco = f"/static/imagens/{nome_arquivo_salvo}"
        from usuarios.gerenciar import atualizar_dados_cadastro, obter_dados_perfil_completo
        
        # Puxa o e-mail atual do usuário para não apagá-lo durante o update da foto
        dados_atuais = obter_dados_perfil_completo(cpf)
        email_atual = dados_atuais.get("email", "")
        
        atualizar_dados_cadastro(cpf, email_atual, url_banco)
        
        return {"sucesso": True, "mensagem": "Foto de perfil atualizada!", "foto_url": url_banco}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")
