class PortariaView:
    @staticmethod
    def resposta_movimentacao(status_msg: str, cartao_id: str) -> dict:
        return {
            "status": status_msg,
            "cartao": cartao_id
        }

    @staticmethod
    def renderizar_dashboard(total_dentro: int, limite_maximo: int) -> dict:
        return {
            "clientes_dentro": total_dentro,
            "vagas_disponiveis": max(0, limite_maximo - total_dentro),
            "status_estabelecimento": "LOTADO" if total_dentro >= limite_maximo else "LIBERADO"
        }