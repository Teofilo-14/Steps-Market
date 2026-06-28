from datetime import datetime

class CaixaView:
    @staticmethod
    def resposta_simples(mensagem: str) -> dict:
        return {"status": mensagem}

    @staticmethod
    def renderizar_recibo(venda_id: int, valor: float, metodo: str) -> dict:
        """Formata o layout oficial do recibo digital (NFCe)"""
        return {
            "mensagem": "Venda concluída com sucesso",
            "recibo": {
                "cupom": f"NFCe-{venda_id:04d}",
                "total_pago": f"R$ {valor:.2f}",
                "forma_pagamento": metodo.upper(),
                "data_emissao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        }

    @staticmethod
    def renderizar_fechamento(status_auditoria: str) -> dict:
        """Formata o relatório visual de fechamento do caixa"""
        return {
            "status": "Caixa encerrado no sistema",
            "relatorio_auditoria": status_auditoria
        }