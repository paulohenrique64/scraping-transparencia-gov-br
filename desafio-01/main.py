import os
import time
import requests

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
    ErroInesperadoDuranteConsulta
)

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
X_API_KEY = os.getenv("X_API_KEY")

app = FastAPI(title="API de Consulta Pessoa Física no Portal da Transparência")

token_em_cache = None
token_expiracao = 0

@app.get("/")
def hello_world():
    return {"message": "hello, world!"}

@app.get("/consulta-pessoa-fisica")
async def consulta_pessoa_fisica(
    identificador: str,
    incluir_filtro_social: bool = Query(default=False),
    user: dict = Depends(get_current_user)
):
    try:
        dados_pessoa = await consultar_dados_pessoa_fisica(identificador, incluir_filtro_social)
        return dados_pessoa

    except (CPFouNISNaoEncontrado, NomeNaoEncontrado, PortalInacessivel, TempoLimiteExcedido) as e:
        return JSONResponse(status_code=422, content={"erro": str(e)})

    except ErroInesperadoDuranteConsulta as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/get-token")
def get_token(x_api_key: str = Header(...)):
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

