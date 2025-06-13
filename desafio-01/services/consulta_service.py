import base64
import json
import os

from pages.portal_page import PortalPage
from playwright.async_api import async_playwright
from dotenv import load_dotenv

from exceptions.scraping_exceptions import (
    ErroInesperadoDuranteConsulta,
    TempoLimiteExcedido,
    PortalInacessivel,
    CPFouNISNaoEncontrado,
    NomeNaoEncontrado,
    ElementoNaoEncontrado,
    FalhaAoColetarDados
)

load_dotenv()

URL_BASE_PORTAL_TRANSPARENCIA = os.getenv("URL_BASE_PORTAL_TRANSPARENCIA")
PATH_BASE_ARMAZENAMENTO_DADOS_PESSOA = os.getenv("PATH_BASE_ARMAZENAMENTO_DADOS_PESSOA")

async def consultar_dados_pessoa_fisica(identificador, aplicar_filtro_social=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            locale='pt-BR',
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9",
                "Referer": f"{URL_BASE_PORTAL_TRANSPARENCIA}"
            },
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        pagina_portal = PortalPage(await context.new_page())

        try:
            search_data = classificar_e_estruturar_identificador(identificador)
            url_resultado = await pagina_portal.buscar_pessoa_fisica(search_data, aplicar_filtro_social)
            dados_pessoa, screenshot_bytes = await pagina_portal.coletar_dados_pessoa_fisica(url_resultado)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            nome_normalizado = dados_pessoa['nome'].lower().replace(" ", "_")
            cpf_fragmento_normalizado = dados_pessoa['cpf'][3:11].replace(".", "_")

            path_pessoa = f"{PATH_BASE_ARMAZENAMENTO_DADOS_PESSOA}/{nome_normalizado}{cpf_fragmento_normalizado}"
            os.makedirs(path_pessoa, exist_ok=True)

            # Salva dados da pessoa
            with open(f"{path_pessoa}/dados.json", "w", encoding="utf-8") as f:
                json.dump(dados_pessoa, f, indent=4, ensure_ascii=False)

            # Salva a imagem em base64 (texto)
            with open(f"{path_pessoa}/screenshot_base64.txt", "w", encoding="utf-8") as f:
                f.write(screenshot_base64)

            # Salva como imagem .png
            with open(f"{path_pessoa}/screenshot.png", "wb") as f:
                f.write(screenshot_bytes)

            dados_pessoa["screenshot_base64"] = screenshot_base64

            return dados_pessoa

        except TempoLimiteExcedido:
            raise
        except (PortalInacessivel, CPFouNISNaoEncontrado, NomeNaoEncontrado, ElementoNaoEncontrado, FalhaAoColetarDados) as e:
            raise e
        except TimeoutError:
            raise TempoLimiteExcedido("Tempo de resposta excedido.")
        except Exception as e:
            raise ErroInesperadoDuranteConsulta(f"Erro inesperado: {e}")
        finally:
            await context.close()
            await browser.close()

def classificar_e_estruturar_identificador(identificador: str):
    tipo = "nome"
    numeros = ''.join(c for c in identificador if c.isdigit())
    
    if len(numeros) == 11:
        tipo = "nis/cpf"

    return {
        "identificador": identificador,
        "tipo": tipo
    }