from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import os
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
ALGORITHMS = ["RS256"]
PROFILE = os.getenv("PROFILE")

http_bearer = HTTPBearer()

def get_jwk():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    return response.json()["keys"]

def verify_jwt(token: str):
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
    if PROFILE == "local":
        return
    
    return verify_jwt(credentials.credentials)
