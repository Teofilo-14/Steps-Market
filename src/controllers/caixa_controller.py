from fastapi import APIRouter
from src.models.caixa_model import CaixaIn, VendaIn, CaixaModel
from src.views.caixa_view import CaixaView

router = APIRouter(prefix="/api/caixa")

@router.post("/abrir")
def abrir(p: CaixaIn):
    CaixaModel.abrir_caixa(p)
    return CaixaView.resposta_simples("Caixa aberto")

@router.post("/venda")
def venda(p: VendaIn):
    # O Model faz a regra e joga pro banco, retornando o ID gerado
    venda_id = CaixaModel.registrar_venda(p)
    # A View monta o layout do recibo com base no ID e nos dados enviados
    return CaixaView.renderizar_recibo(venda_id, p.valor, p.metodo)

@router.post("/fechar")
def fechar(p: CaixaIn):
    resultado_auditoria = CaixaModel.fechar_caixa(p)
    # A View monta o relatório final do fechamento
    return CaixaView.renderizar_fechamento(resultado_auditoria)