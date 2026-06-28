from ..models.fila_model import ClienteFila

class FilaView:
    @staticmethod
    def renderizar_cliente(cliente) -> dict:
        return {
            "senha": cliente.senha,
            "nome": cliente.nome,
            "status": cliente.status,
            "horario_gerado": cliente.horario_gerado
        }

    @staticmethod
    def renderizar_dashboard(dados_fila: dict) -> dict:
        return dados_fila

    @staticmethod
    def resposta_sucesso(mensagem: str) -> dict:
        return {
            "status": "sucesso",
            "mensagem": mensagem
        }