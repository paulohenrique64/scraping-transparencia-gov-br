https://portaldatransparencia.gov.br/pessoa/visao-geral


  File "/home/paulo-henrique/tmp/projeto-hiperautomacao-MOST/.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py", line 528, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.Error: Locator.click: Error: strict mode violation: locator(".dataTables_length").locator("select") resolved to 2 elements:
    1) <select class="form-control input-sm" name="tabelaDetalheValoresRecebidos_length" aria-controls="tabelaDetalheValoresRecebidos">…</select> aka get_by_role("combobox")
    2) <select class="form-control input-sm" name="tabelaDetalheValoresSacados_length" aria-controls="tabelaDetalheValoresSacados">…</select> aka locator("select[name=\"tabelaDetalheValoresSacados_length\"]")

Call log:
  - waiting for locator(".dataTables_length").locator("select")