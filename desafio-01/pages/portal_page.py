import asyncio
import os
from dotenv import load_dotenv

from exceptions.scraping_exceptions import (
    CPFouNISNaoEncontrado,
    NomeNaoEncontrado,
    PortalInacessivel,
    TempoLimiteExcedido,
    ElementoNaoEncontrado,
    FalhaAoColetarDados
)

load_dotenv()

url_base_portal_transparencia = os.getenv("URL_BASE_PORTAL_TRANSPARENCIA")
tipos_recebimentos_permitidos =  os.getenv("TIPOS_RECEBIMENTO_PERMITIDOS").split(",")

class PortalPage:
    def __init__(self, page):
        self.page = page
    
    async def buscar_pessoa_fisica(self, search_data, aplicar_filtro_social):
        try:
            await self.page.goto(f"{url_base_portal_transparencia}/pessoa/visao-geral", wait_until="load")
        except Exception:
            raise PortalInacessivel("Não foi possível acessar o Portal da Transparência.")

        try:
            await asyncio.sleep(5)
            await self.page.locator("#button-consulta-pessoa-fisica").click()
            await asyncio.sleep(5)
            await self.page.locator("#accept-all-btn").click()
            await asyncio.sleep(5)
            await self.page.locator("#termo").fill(search_data["identificador"])
        except Exception:
            raise ElementoNaoEncontrado("Erro ao preencher ou localizar o campo de busca.")
        
        try:
            if aplicar_filtro_social:
                await asyncio.sleep(5)
                await self.page.get_by_role("button", name="Refine a Busca").click()
                await asyncio.sleep(5)
                await self.page.click('label[for="beneficiarioProgramaSocial"]')
                await asyncio.sleep(5)
                await self.page.click("#btnConsultarPF")
            else:
                await self.page.locator(".busca-indice").locator("[type=submit]").click()
            await asyncio.sleep(5)
        except Exception:
            raise TempoLimiteExcedido("A ação de busca excedeu o tempo esperado.")

        url_resultado = None
        avancos_proxima_pagina_cont = 0

        # busca por nome
        if search_data["tipo"] == "nome":
            try:
                avancar_para_proxima_pagina = True

                while avancar_para_proxima_pagina == True:
                    listitem = self.page.locator("#resultados").get_by_role("listitem") 
                    listitem_count = await listitem.count()
                    pagina_atual_url_resultados = []

                    for i in range(listitem_count):
                        item = listitem.nth(i)
                        link = await item.locator("a").get_attribute("href")
                        nome = await item.locator(".link-busca-nome").inner_html()
                        pagina_atual_url_resultados.append(nome.lower())

                        if nome.lower().strip() == search_data["identificador"].lower().strip():
                            url_resultado = (f'{url_base_portal_transparencia}{link}')

                    avancar_para_proxima_pagina = True

                    # será possível ir para a proxima pagina se:
                    #   - o nome nao for encontrado na pagina atual em 2 buscas
                    #   - existir proxima pagina
                    for nome in pagina_atual_url_resultados:
                        if nome.lower().strip() == search_data["identificador"].lower().strip():
                            avancar_para_proxima_pagina = False
                    
                    next_button = self.page.locator("#paginacao").locator('.pagination li[class$="next"]')

                    if avancos_proxima_pagina_cont > 2 \
                        or await next_button.count() == 0 \
                        or await self.page.locator("#boxPaginacaoBuscaLista").get_attribute("style") == "display: none;":
                        avancar_para_proxima_pagina = False
        
                    if avancar_para_proxima_pagina == True:
                        await self.page.get_by_text("Próxima").click()
                        await asyncio.sleep(10)
                        avancos_proxima_pagina_cont = avancos_proxima_pagina_cont + 1
                    else:
                        if url_resultado == None:
                            raise NomeNaoEncontrado(f"Foram encontrados 0 resultados para o termo {search_data["identificador"]}")
                        return url_resultado
            except Exception:
                raise ElementoNaoEncontrado("Erro ao navegar pelos resultados da busca por nome.")

        # buscando por cpf ou nis
        try:
            listitem = self.page.locator("#resultados").get_by_role("listitem") 
            listitem_count = await listitem.count()

            for i in range(listitem_count):
                item = listitem.nth(i)
                link = await item.locator("a").get_attribute("href")
                nome = await item.locator(".link-busca-nome").inner_html()
                url_resultado = f'{url_base_portal_transparencia}{link}'

            if url_resultado is None:
                raise CPFouNISNaoEncontrado(f"Não foi possível retornar os dados no tempo de resposta solicitado")
            return url_resultado
        except Exception:
            raise ElementoNaoEncontrado("Erro ao processar os resultados da busca por CPF ou NIS.")
    
    async def coletar_dados_pessoa_fisica(self, url_pagina_pessoa_encontrada):
        try:
            await asyncio.sleep(10)
            await self.page.goto(url_pagina_pessoa_encontrada, wait_until="load")
            await asyncio.sleep(5)
            
            dados_pessoa = {}

            strongs = self.page.locator(".dados-tabelados").locator("strong")
            spans = self.page.locator(".dados-tabelados").locator("span")

            for i in range(3):
                strong = strongs.nth(i)
                span = spans.nth(i)

                strong_data = await strong.inner_html()
                span_data = await span.inner_html()

                dados_pessoa[strong_data.lower()] = span_data.strip()
        except Exception:
            raise FalhaAoColetarDados("Não foi possível coletar os dados da página da pessoa.")

        try:
            await self.page.get_by_role("button", name="Recebimentos de recursos").click()
            await self.page.locator("#cookiebar-modal-footer-buttons").locator("#accept-all-btn").click()
            screenshot_bytes = await self.page.screenshot()
        except Exception:
            raise ElementoNaoEncontrado("Erro ao acessar os dados de recebimentos.")

        try:
            recebimentos_elements = self.page.locator(".box-ficha__resultados").locator(".br-table")
            count_recebimentos_elements = await recebimentos_elements.count()
            recebimentos = []

            for i in range(count_recebimentos_elements):
                elemento = recebimentos_elements.nth(i)
                tipo = (await elemento.locator("strong").inner_html()).lower()
                valor_recebido = await elemento.locator("tbody >> td:nth-child(4)").inner_html()

                # verifica se tipo é permitido
                if not any(tipo_permitido in tipo for tipo_permitido in tipos_recebimentos_permitidos):
                    continue

                recebimento = {
                    "tipo": tipo,
                    "valor_recebido": valor_recebido.strip()
                }

                recurso_path = await elemento.locator("a").get_attribute("href")
                recurso_url = f"{url_base_portal_transparencia}{recurso_path}"

                recebimento["recursos"] = await self.__coletar_recursos_pessoa_fisica__(recurso_url)
                recebimentos.append(recebimento)

                # retorna para a página anterior
                await self.page.go_back()
                await asyncio.sleep(15)

            dados_pessoa["recebimentos"] = recebimentos
            return dados_pessoa, screenshot_bytes
        except Exception:
            raise FalhaAoColetarDados("Erro ao coletar os dados de recebimentos.")
    
    async def __coletar_recursos_pessoa_fisica__(self, recurso_url):
        try:
            await asyncio.sleep(10)
            await self.page.goto(recurso_url, wait_until="load")
            await asyncio.sleep(5)
        except Exception:
            raise PortalInacessivel("Erro ao acessar página de detalhes do recurso.")

        recursos_totais = []
        try:
            dados_detalhados_list = self.page.locator(".dados-detalhados")
            dados_detalhados_list_count = await dados_detalhados_list.count()

            # loop for por cada tabela
            for i in range(dados_detalhados_list_count):
                dados_detalhados = dados_detalhados_list.nth(i)
                recursos = []
                tem_proxima_pagina = True

                if i != 0:
                    await dados_detalhados.click()
            
                while tem_proxima_pagina == True:
                    rows_list = dados_detalhados.get_by_role("row")
                    recursos_count = await rows_list.count()
                    
                    if len(recursos) == 0:
                        row = rows_list.nth(0)
                        ths = row.locator("th")
                        count_ths = await ths.count()
                        cabecalho = []

                        for i in range(count_ths):
                            cabecalho.append(await ths.nth(i).inner_html())

                        recursos.append(cabecalho)

                    for i in range(1, recursos_count):
                        row = rows_list.nth(i)
                        spans = row.locator("span")
                        recurso = []

                        count_span = await spans.count()
                
                        for j in range(count_span):
                            span = spans.nth(j)
                            data = await span.inner_html()
                            recurso.append(data) 

                        recursos.append(recurso)

                    next_button = dados_detalhados.locator('.box-paginacao li[id$="_next"][class$="disabled"]')

                    if await next_button.count() > 0:
                        tem_proxima_pagina = False
                    else:
                        await dados_detalhados.locator('.box-paginacao li[id$="_next"]').click()
                        await asyncio.sleep(5)
                        tem_proxima_pagina = True

                recursos_totais.append(recursos)
            return recursos_totais
        except Exception:
            raise FalhaAoColetarDados("Erro ao coletar os recursos detalhados.")