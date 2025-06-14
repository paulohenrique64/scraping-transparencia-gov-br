import pytz
import requests
import time
import os

from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from services.consulta_service import consultar_dados_pessoa_fisica
from services.auth_service import get_current_user
from dotenv import load_dotenv

from exceptions.scraping_exceptions import (
    CPFouNISNaoEncontrado,
    NomeNaoEncontrado,
    PortalInacessivel,
    TempoLimiteExcedido,
    ErroInesperadoDuranteConsulta,
    ElementoNaoEncontrado,
    FalhaAoColetarDados
)

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
X_API_KEY = os.getenv("X_API_KEY")

app = FastAPI(
    title="API de Consulta Pessoa Física no Portal da Transparência",
    description="API para consultar dados de pessoa física no Portal da Transparência com autenticação via OAuth2 (Auth0).",
    version="1.0.0",
    docs_url="/docs",      
)

token_em_cache = None
token_expiracao = 0


@app.get("/", summary="Endpoint de teste", tags=["Geral"])
def hello_world():
    """
    Endpoint simples para verificar se a API está no ar.
    """
    return {"message": "hello, world!"}


@app.get(
    "/consulta-pessoa-fisica",
    summary="Consulta dados de pessoa física",
    tags=["Consulta"],
    response_description="Dados detalhados da pessoa física consultada",
    responses={
        200: {"description": "Consulta realizada com sucesso"},
        422: {"description": "Erro na consulta: dados não encontrados ou limite excedido"},
        500: {"description": "Erro inesperado no servidor"},
        401: {"description": "Usuário não autenticado"},
    }
)
async def consulta_pessoa_fisica(
    identificador: str = Query(..., description="Nome, CPF ou NIS da pessoa a ser consultada"),
    incluir_filtro_social: bool = Query(default=False, description="Incluir filtro social na consulta"),
    user: dict = Depends(get_current_user)
):
    agora = datetime.now(pytz.timezone("America/Sao_Paulo"))
    print(f"[{agora.strftime('%H:%M:%S')}] Identificador recebido para busca: {identificador}")
    
    try:
        dados_pessoa = await consultar_dados_pessoa_fisica(identificador, incluir_filtro_social)
        return dados_pessoa

    except (CPFouNISNaoEncontrado, NomeNaoEncontrado, PortalInacessivel, TempoLimiteExcedido) as e:
        return JSONResponse(status_code=422, content={"erro": str(e)})

    except ErroInesperadoDuranteConsulta as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})


@app.get(
    "/get-token",
    summary="Gera token de acesso via chave de API",
    tags=["Autenticação"],
    response_description="Token de acesso válido para consumir endpoints protegidos",
    responses={
        200: {"description": "Token gerado com sucesso"},
        401: {"description": "Chave de API inválida"},
    }
)
def get_token(x_api_key: str = Header(..., description="Chave de API para autorização")):
    if x_api_key != X_API_KEY:
        raise HTTPException(status_code=401, detail="Chave para geração de token inválida.")

    global token_em_cache, token_expiracao
    now = time.time()

    if token_em_cache and now < token_expiracao:
        return {"access_token": token_em_cache}

    resp = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": f"{CLIENT_ID}",
            "client_secret": f"{CLIENT_SECRET}",
            "audience": f"{AUTH0_API_AUDIENCE}",
            "grant_type": "client_credentials"
        }
    )
    resp.raise_for_status()
    data = resp.json()

    token_em_cache = data["access_token"]
    token_expiracao = now + 86000
    
    return {"access_token": data["access_token"]}

