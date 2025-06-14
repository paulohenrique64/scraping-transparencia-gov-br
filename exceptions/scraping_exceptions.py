class ErroConsultaPortal(Exception):
    """Exceção base para todos os erros relacionados à consulta."""
    pass

class NomeNaoEncontrado(ErroConsultaPortal):
    """Nome consultado não retornou resultados."""
    pass

class CPFouNISNaoEncontrado(ErroConsultaPortal):
    """CPF ou NIS consultado não retornou resultados."""
    pass

class PortalInacessivel(ErroConsultaPortal):
    """Não foi possível acessar o Portal da Transparência."""
    pass

class TempoLimiteExcedido(ErroConsultaPortal):
    """Tempo de resposta excedido durante a automação."""
    pass

class ElementoNaoEncontrado(ErroConsultaPortal):
    """Elemento esperado na página não foi encontrado (pode ter mudado o site)."""
    pass

class FalhaAoColetarDados(ErroConsultaPortal):
    """Erro ao coletar os dados da pessoa na tela de detalhes."""
    pass

class ErroInesperadoDuranteConsulta(ErroConsultaPortal):
    """Qualquer outro erro inesperado."""
    pass
