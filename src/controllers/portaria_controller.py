from fastapi import APIRouter
from ..models.portaria_model import PortariaModel
from ..views.portaria_view import PortariaView

router = APIRouter(prefix="/api/portaria")

@router.get("/dashboard")
def rota_dashboard():
    dentro = PortariaModel.obter_total_dentro()
    return PortariaView.renderizar_dashboard(dentro, PortariaModel.LIMITE_MAXIMO)

@router.post("/entrada/{cartao_id}")
def rota_entrada(cartao_id: str):
    cartao_processado = PortariaModel.registrar_entrada(cartao_id)
    return PortariaView.resposta_movimentacao("Entrada liberada", cartao_processado)

@router.post("/saida/{cartao_id}")
def rota_saida(cartao_id: str):
    cartao_processado = PortariaModel.registrar_saida(cartao_id)
    return PortariaView.resposta_movimentacao("Saída processada, vaga liberada", cartao_processado)