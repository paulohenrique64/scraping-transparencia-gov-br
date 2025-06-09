import asyncio
from playwright.async_api import async_playwright
from pages.portal_page import PortalPage

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            locale='pt-BR',
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9",
                "Referer": "https://portaldatransparencia.gov.br/"
            }
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        page = await context.new_page()
        teste = PortalPage(page, "Paulo Henrique")
        await teste.consultar_pessoa_fisica()

        await context.close()
        await browser.close()

asyncio.run(main())