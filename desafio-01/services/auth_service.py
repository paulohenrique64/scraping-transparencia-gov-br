import requests
import os

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN") # Domínio da instância Auth0
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE") # Identificador da API configurado no painel do Auth0
ALGORITHMS = ["RS256"] # Algoritmo usado para assinar os tokens JWT
PROFILE = os.getenv("PROFILE", "prod") # Ambiente de execução: "local" ou "prod" (default = "prod")

http_bearer = HTTPBearer()

def get_jwk():
    """
    Obtém as chaves públicas (JWKs) do endpoint do Auth0 para verificação dos tokens JWT.
    """
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    return response.json()["keys"]

def verify_jwt(token: str):
    """
    Valida o JWT recebido:
    - Obtém o cabeçalho sem verificar a assinatura.
    - Busca a chave pública correspondente (com base no 'kid' do cabeçalho).
    - Usa a chave para decodificar e validar o token.
    - Verifica o emissor (issuer) e o público (audience).

    Parâmetros:
        token (str): JWT a ser validado.

    Retorna:
        dict: Payload decodificado do JWT se válido.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
        jwks = get_jwk()

        rsa_key = {}
        for key in jwks:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Chave pública não encontrada.")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido.")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(http_bearer)):
    """
    Dependency utilizada pelo FastAPI para proteger rotas com autenticação JWT via Auth0.

    - Em ambiente local (`PROFILE=local`), a autenticação é ignorada.
    - Em produção, valida o token com o Auth0.

    Parâmetros:
        credentials (HTTPAuthorizationCredentials): Token JWT extraído do cabeçalho Authorization.

    Retorna:
        dict: Payload decodificado do usuário autenticado (em produção).
    """
    if PROFILE == "local":
        return
    
    return verify_jwt(credentials.credentials)
