import base64
from pages.portal_page import PortalPage
import json
import os
from playwright.async_api import async_playwright

async def consulta_pessoa_fisica(search_data, social_filter, data_screenshot):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            locale='pt-BR',
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9",
                "Referer": "https://portaldatransparencia.gov.br/"
            },
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        portal_page = PortalPage(await context.new_page())

        try:
            matched_person_url = await portal_page.buscar_pessoa_fisica(search_data, social_filter)

            person_data, screenshot_bytes = await portal_page.coletar_dados_pessoa_fisica(matched_person_url)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            person_storage_dirname = f"./data/{person_data['nome'].lower().replace(" ", "_")}{person_data['cpf'][3:11].replace(".", "_")}"
            os.makedirs(f"{person_storage_dirname}", exist_ok=True)

            # salva os dados da pessoa
            with open(f"{person_storage_dirname}/data.json", "w", encoding="utf-8") as f:
                json.dump(person_data, f, indent=4, ensure_ascii=False)
                
            # salva a imagem codificada em base64 (em formato texto)
            with open(f"{person_storage_dirname}/screenshot_base64.txt", "w", encoding="utf-8") as f:
                f.write(screenshot_base64)

            # salva como imagem real .png:
            with open(f"{person_storage_dirname}/screenshot.png", "wb") as f:
                f.write(screenshot_bytes)

            if data_screenshot == True:
                person_data["base64_screenshot"] = screenshot_base64

            return person_data
        except RuntimeError as r:
            print(f"{r}")

        await context.close()
        await browser.close()