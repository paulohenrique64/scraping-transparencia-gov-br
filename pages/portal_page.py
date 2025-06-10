import asyncio

class PortalPage:
    def __init__(self, page):
        self.page = page
    
    async def buscar_pessoa_fisica(self, search_data):
        await self.page.goto("https://portaldatransparencia.gov.br/pessoa/visao-geral")
        await self.page.locator("#button-consulta-pessoa-fisica").click()
        await self.page.locator("#termo").fill(search_data["data"])
        await self.page.locator("#accept-all-btn").click()
        await asyncio.sleep(3)
        await self.page.get_by_role("button", name="Refine a Busca").click()
        await self.page.click('label[for="beneficiarioProgramaSocial"]')
        await self.page.click("#btnConsultarPF")
        await asyncio.sleep(3)

        matched_person_urls = []

        # buscando por nome
        if search_data["type"] == "nome":
            can_go_to_next_page = True

            while can_go_to_next_page == True:
                listitem = self.page.locator("#resultados").get_by_role("listitem") 
                listitem_count = await listitem.count()
                current_page_matched_person_urls = []

                for i in range(listitem_count):
                    item = listitem.nth(i)
                    link = await item.locator("a").get_attribute("href")
                    name = await item.locator(".link-busca-nome").inner_html()
                    current_page_matched_person_urls.append(name.lower())
                    matched_person_urls.append(f'https://portaldatransparencia.gov.br{link}')

                if search_data["type"] == "nome":
                    can_go_to_next_page = True
                    
                can_go_to_next_page = False
                for name in current_page_matched_person_urls:
                    if name == self.person_data.lower():
                        can_go_to_next_page = True
                
                if can_go_to_next_page == True:
                    await self.page.get_by_text("Próxima").click()
                    await asyncio.sleep(10)
                else:
                    return matched_person_urls

        # buscando por cpf ou nis
        listitem = self.page.locator("#resultados").get_by_role("listitem") 
        listitem_count = await listitem.count()

        for i in range(listitem_count):
            item = listitem.nth(i)
            link = await item.locator("a").get_attribute("href")
            name = await item.locator(".link-busca-nome").inner_html()
            matched_person_urls.append(f'https://portaldatransparencia.gov.br{link}')

        return matched_person_urls
    
    async def coletar_dados_pessoa_fisica(self, person_url):
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

        await self.page.locator("#cookiebar-modal-footer-buttons").locator("#accept-all-btn").click()
        screenshot_bytes = await self.page.screenshot()
        
        for i in range(count_recebimentos_elements):
            recebimento = {}
            tipo = await recebimentos_elements.nth(i).locator("strong").inner_html()
            valor_recebido = await recebimentos_elements.nth(i).locator("tbody").locator("td").nth(3).inner_html()

            recebimento["tipo"] = tipo
            recebimento["valor_recebido"] = valor_recebido.strip()
            recebimento_recurso_url = f"https://portaldatransparencia.gov.br{await recebimentos_elements.nth(i).locator("a").get_attribute("href")}"

            recursos = await self.__coletar_recursos_pessoa_fisica__(recebimento_recurso_url)
            recebimento["recursos"] = recursos
            recebimentos.append(recebimento)

            # Voltando para a página da pessoa física selecionada
            await self.page.go_back()
            await asyncio.sleep(5)

        person_data["recebimentos"] = recebimentos
        return person_data, screenshot_bytes
    
    async def __coletar_recursos_pessoa_fisica__(self, recurso_url):
        await asyncio.sleep(10)
        await self.page.goto(recurso_url, wait_until="load")
        await asyncio.sleep(5)
        await self.page.locator(".dataTables_length").locator("select").click()
        await self.page.select_option('select[name$="_length"]', '30')
        await asyncio.sleep(5)

        recursos = []
        has_next_page = True
        
        while has_next_page == True:
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
                has_next_page = False
            else:
                await self.page.locator('.box-paginacao li[id$="_next"]').click()
                await asyncio.sleep(5)
                has_next_page = True

        return recursos