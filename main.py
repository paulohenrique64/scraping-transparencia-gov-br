from fastapi import FastAPI
from fastapi.responses import JSONResponse
from exceptions.scraping_exceptions import CPFouNISNaoEncontrado, NomeNaoEncontrado
from services.consulta_service import consulta_pessoa_fisica

app = FastAPI(title="API de Consulta Pessoa Física")

@app.get("/consulta-pessoa-fisica")
async def consulta(search_data: str):
    try:
        person_data = await consulta_pessoa_fisica(search_data_classifier_and_builder(search_data))
        return person_data
    except (CPFouNISNaoEncontrado, NomeNaoEncontrado) as e:
        return JSONResponse(status_code=422, content={"erro": str(e)})


def search_data_classifier_and_builder(search_data: str):
    type = "nome"
    numeros = ''.join(c for c in search_data if c.isdigit())
    
    if len(numeros) == 11:
        type = "nis/cpf"

    return {
        "data": search_data,
        "type": type
    }