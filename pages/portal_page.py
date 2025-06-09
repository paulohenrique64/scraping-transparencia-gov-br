import asyncio
from pprint import pprint
import os
import json

class PortalPage:
    def __init__(self, page, person_data):
        self.page = page
        self.person_data = person_data

    async def consultar_pessoa_fisica(self):
        #
        #
        # Página para busca de pessoas físicas
        #
        #
        await self.page.goto("https://portaldatransparencia.gov.br/pessoa/visao-geral")
        await self.page.locator("#button-consulta-pessoa-fisica").click()
        await self.page.locator("#termo").fill(self.person_data)
        await self.page.locator("#accept-all-btn").click()
        await asyncio.sleep(3)
        await self.page.get_by_role("button", name="Refine a Busca").click()
        await self.page.click('label[for="beneficiarioProgramaSocial"]')
        await self.page.click("#btnConsultarPF")
        await asyncio.sleep(3)

        person_founded_url_list = []
        next = True

        while next == True:
            lista = self.page.locator("#resultados").get_by_role("listitem") 
            count = await lista.count()
            current_person_founded_name_list = []

            for i in range(count):
                item = lista.nth(i)
                link = await item.locator("a").get_attribute("href")
                name = await item.locator(".link-busca-nome").inner_html()
                current_person_founded_name_list.append(name.lower())
                person_founded_url_list.append(f'https://portaldatransparencia.gov.br{link}')
                
            next = False
            for name in current_person_founded_name_list:
                if name == self.person_data.lower():
                    next = True
            
            if next == True:
                # next logic
                await self.page.get_by_text("Próxima").click()
                await asyncio.sleep(10)

        print(person_founded_url_list)

        #
        #
        # Página da pessoa física selecionada
        #
        #
        for person_url in person_founded_url_list:
            await asyncio.sleep(10)
            await self.page.goto(person_url)
            await asyncio.sleep(5)
            
            person_data = {}

            strongs_dados_tabelados = self.page.locator(".dados-tabelados").locator("strong")
            spans_dados_tabelados = self.page.locator(".dados-tabelados").locator("span")

            for i in range(3):
                strong = strongs_dados_tabelados.nth(i)
                span = spans_dados_tabelados.nth(i)

                strong_data = await strong.inner_html()
                span_data = await span.inner_html()

                person_data[strong_data.lower()] = span_data.strip()

            await self.page.get_by_role("button", name="Recebimentos de recursos").click()

            recebimentos_elements = self.page.locator(".box-ficha__resultados").locator(".br-table")
            count_recebimentos_elements = await recebimentos_elements.count()
            recebimentos = []
            person_data_storage_path = f"{person_data['nome'].lower().replace(" ", "_")}{person_data['cpf'][3:11].replace(".", "_")}"
            os.makedirs(f"./data/{person_data_storage_path}", exist_ok=True)
            
            await self.page.locator("#cookiebar-modal-footer-buttons").locator("#accept-all-btn").click()
            await self.page.screenshot(path=f"./data/{person_data_storage_path}/screenshot_person_data.png", full_page=True)
            
            for i in range(count_recebimentos_elements):
                recebimento = {}
                tipo = await recebimentos_elements.nth(i).locator("strong").inner_html()
                valor_recebido = await recebimentos_elements.nth(i).locator("tbody").locator("td").nth(3).inner_html()

                recebimento["tipo"] = tipo
                recebimento["valor_recebido"] = valor_recebido.strip()

                #
                #
                # Página do recebimento de um recurso (ex: auxílio emergencial)
                #
                #
                detalhar_recebimento_page_link = await recebimentos_elements.nth(i).locator("a").get_attribute("href")
                
                await asyncio.sleep(10)
                await self.page.goto(f'https://portaldatransparencia.gov.br{detalhar_recebimento_page_link}', wait_until="load")
                await asyncio.sleep(5)
                await self.page.locator(".dataTables_length").locator("select").click()
                await self.page.select_option('select[name$="_length"]', '30')
                await asyncio.sleep(5)

                recursos = []
                exist_next_page = True
                
                while exist_next_page == True:
                    lista_rows = self.page.locator(".dados-detalhados").get_by_role("row")
                    count_recursos = await lista_rows.count()
                    
                    if len(recursos) == 0:
                        row = lista_rows.nth(0)
                        ths = row.locator("th")
                        count_ths = await ths.count()
                        cabecalho = []

                        for i in range(count_ths):
                            cabecalho.append(await ths.nth(i).inner_html())

                        recursos.append(cabecalho)

                    for i in range(count_recursos):
                        # pular cabeçalho
                        if i == 0:
                            continue

                        row = lista_rows.nth(i)
                        spans = row.locator("span")
                        recurso = []

                        count_span = await spans.count()
                
                        for j in range(count_span):
                            span = spans.nth(j)
                            data = await span.inner_html()
                            recurso.append(data) 

                        recursos.append(recurso)
                    
                    next_button = self.page.locator('.box-paginacao li[id$="_next"][class$="disabled"]')

                    if await next_button.count() > 0:
                        exist_next_page = False
                    else:
                        await self.page.locator('.box-paginacao li[id$="_next"]').click()
                        await asyncio.sleep(5)
                        exist_next_page = True
                    
                for recurso in recursos:
                    print(recurso)

                recebimento["recursos"] = recursos
                recebimentos.append(recebimento)

                #
                #
                # Voltando para a página da pessoa física selecionada
                #
                #
                await self.page.go_back()
                await asyncio.sleep(5)

            person_data["recebimentos"] = recebimentos
            pprint(person_data)
            with open(f"./data/{person_data_storage_path}/data.json", "w", encoding="utf-8") as f:
                json.dump(person_data, f, indent=4, ensure_ascii=False)