class UsuarioView:
    @staticmethod
    def resposta_sucesso(mensagem: str) -> dict:
        return {
            "status": "Operação Realizada",
            "detalhes": mensagem
        }