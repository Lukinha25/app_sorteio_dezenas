import os
import requests
import secrets

# CONFIGURAÇÕES DA SUA CONTA PJ INTER (Substitua quando pegar no painel do banco)
INTER_CLIENT_ID = "seu_client_id_aqui"
INTER_CLIENT_SECRET = "seu_client_secret_aqui"
INTER_CHAVE_PIX_EVP = "sua_chave_pix_inter_aqui" # Pode ser o CNPJ ou Chave Aleatória

# Caminhos dos arquivos de segurança mTLS
CAMINHO_CERT = "credenciais_banco/certificado.crt"
CAMINHO_KEY = "credenciais_banco/chave_privada.key"

def obter_token_autorizacao_inter() -> str:
    """Faz a autenticação segura mTLS no Banco Inter para liberar o uso do Pix."""
    url = "https://inter.co"
    payload = {
        "grant_type": "client_credentials",
        "scope": "pix.read pix.write"
    }
    try:
        # O banco exige passar o certificado físico (.crt e .key) junto na requisição
        certificados = (CAMINHO_CERT, CAMINHO_KEY)
        resposta = requests.post(url, data=payload, cert=certificados, timeout=10)
        if resposta.status_code == 200:
            return resposta.json().get("access_token")
        return ""
    except Exception:
        return ""

def  gerar_qrcode_pix_inter_real(valor: float, cpf_usuario: str) -> dict:
    """
    Solicita uma cobrança PIX imediata ao Banco Inter.
    Retorna o código Copia e Cola e o QR Code.
    """
    token = obter_token_autorizacao_inter()
    
    # SIMULAÇÃO DE SEGURANÇA (Se você não tiver as chaves do Inter ainda)
    if not token or INTER_CLIENT_ID == "seu_client_id_aqui":
        txid_falso = f"TXID{secrets.token_hex(13).upper()}"
        copia_e_cola_falso = f"00020101021226830014br.gov.bcb.pix2561api.inter.co/v2/cobv/{txid_falso}5204000053039865405{valor:.2f}5802BR5907Lukinha6004Luz62070503***6304"
        
               # Corrigido o caractere escondido do link para o navegador ler de primeira
        link_qrcode_perfeito = f"https://qrserver.com{copia_e_cola_falso}"
        
        return {
            "sucesso": True,
            "simulado": True,
            "txid": txid_falso,
            "pix_copia_cola": copia_e_cola_falso,
            "qrcode_base64_url": link_qrcode_perfeito
        }

    # SE TIVER AS CREDENCIAIS REAIS, O CÓDIGO ABAIXO SE CONECTA DIRETO COM O BANCO INTER:
    url_cob = "https://inter.co"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # O Banco Inter exige um identificador único de 26 a 35 caracteres para cada Pix (O TXID)
    txid_exclusivo = f"LUKINHA{secrets.token_hex(12).upper()}"
    
    payload = {
        "calendario": {"expiracao": 3600}, # Pix expira em 1 hora
        "devedor": {"cpf": cpf_usuario, "nome": "Cliente Aplicativo"},
        "valor": {"original": f"{valor:.2f}"},
        "chave": INTER_CHAVE_PIX_EVP,
        "solicitacaoPagador": "Deposito Saldo Aplicativo Sorteio"
    }

    try:
        certificados = (CAMINHO_CERT, CAMINHO_KEY)
        # 1. Cria a ordem de cobrança do Pix de R$ 20 dentro do Banco Inter
        resposta_cob = requests.put(f"{url_cob}/{txid_exclusivo}", json=payload, cert=certificados, timeout=10)
        
        if resposta_cob.status_code == 201:
            dados_cob = resposta_cob.json()
            pix_copia_cola = dados_cob.get("pixCopiaECola")
            
            # 2. Busca a imagem do QR code correspondente a esse Pix criado
            url_qrcode = f"https://inter.co/{txid_exclusivo}/qrcode"
            resposta_qr = requests.get(url_qrcode, headers=headers, cert=certificados, timeout=10)
            
            qrcode_url = ""
            if resposta_qr.status_code == 200:
                # O Inter retorna a imagem pronta ou em formato base64
                qrcode_url = resposta_qr.json().get("imagemBase64", "")
            
            return {
                "sucesso": True,
                "simulado": False,
                "txid": txid_exclusivo,
                "pix_copia_cola": pix_copia_cola,
                "qrcode_base64_url": qrcode_url if qrcode_url else "https://wikimedia.org"
            }
            
        return {"sucesso": False, "erro": "Banco Inter recusou a criação do PIX."}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}
