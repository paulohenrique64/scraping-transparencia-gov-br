from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse
from services.consulta_service import consultar_dados_pessoa_fisica
from services.auth_service import get_current_user

from exceptions.scraping_exceptions import (
    CPFouNISNaoEncontrado,
    NomeNaoEncontrado,
    PortalInacessivel,
    TempoLimiteExcedido,
    ErroInesperadoDuranteConsulta
)

app = FastAPI(title="API de Consulta Pessoa Física no Portal da Transparência")

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