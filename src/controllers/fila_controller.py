from fastapi import APIRouter
from ..models.fila_model import RequisicaoCliente, FilaModel
from ..views.fila_view import FilaView

router = APIRouter(prefix="/api/fila")

@router.get("/dashboard")
def rota_dashboard():
    dados = FilaModel.buscar_dados_fila()
    return FilaView.renderizar_dashboard(dados)

@router.post("/senha/gerar", status_code=201)
def rota_gerar_senha(payload: RequisicaoCliente):
    novo_cliente = FilaModel.emitir_nova_senha(payload.nome)
    return FilaView.renderizar_cliente(novo_cliente)

@router.post("/painel/chamar")
def rota_chamar():
    cliente_chamado = FilaModel.chamar_proximo_cliente()
    return FilaView.renderizar_cliente(cliente_chamado)

@router.put("/painel/confirmar")
def rota_confirmar():
    FilaModel.confirmar_entrada_cliente()
    return FilaView.resposta_sucesso("Entrada validada com sucesso.")

@router.put("/clientes/saida")
def rota_saida():
    FilaModel.registrar_saida_cliente()
    return FilaView.resposta_sucesso("Saída processada, vaga liberada.")