class ProdutoView:
    @staticmethod
    def resposta_sucesso(mensagem: str) -> dict:
        return {"status": "sucesso", "mensagem": mensagem}

    @staticmethod
    def renderizar_baixa_estoque(dados_baixa: dict) -> dict:
        status_estoque = "NORMAL"
        if dados_baixa["restante"] == 0:
            status_estoque = "⚠️ CRÍTICO: PRODUTO ESGOTADO!"
        elif dados_baixa["restante"] <= dados_baixa["minimo"]:
            status_estoque = "⚠️ ATENÇÃO: Estoque abaixo do mínimo!"

        return {
            "produto": dados_baixa["nome"],
            "quantidade_restante": dados_baixa["restante"],
            "alerta_status": status_estoque
        }

    @staticmethod
    def renderizar_relatorio_alertas(produtos_criticos: list) -> dict:
        return {
            "total_produtos_em_risco": len(produtos_criticos),
            "produtos": [
                {"id": p["id"], "nome": p["nome"], "atual": p["quantidade"], "minimo": p["estoque_minimo"]}
                for p in produtos_criticos
            ]
        }