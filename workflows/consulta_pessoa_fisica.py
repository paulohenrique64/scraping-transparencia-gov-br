import base64
import json
import os
from pages.portal_page import PortalPage

async def consulta_pessoa_fisica(page, search_data):
    portal_page_1 = PortalPage(page)
    matched_person_urls = await portal_page_1.buscar_pessoa_fisica(search_data)

    for person_url in matched_person_urls:
        person_data, screenshot_bytes = await portal_page_1.coletar_dados_pessoa_fisica(person_url)
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