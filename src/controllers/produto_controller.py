from fastapi import APIRouter
from ..models.produto_model import ProdutoIn, ProdutoModel
from ..views.produto_view import ProdutoView

router = APIRouter(prefix="/api/produtos")

@router.post("/cadastrar", status_code=201)
def cadastrar(payload: ProdutoIn):
    ProdutoModel.cadastrar_produto(payload)
    return ProdutoView.resposta_sucesso("Produto adicionado ao estoque.")

@router.post("/{produto_id}/vender/{quantidade}")
def vender_produto(produto_id: int, quantidade: int):
    # O Model altera o banco e valida a quantidade
    dados_baixa = ProdutoModel.simular_venda_produto(produto_id, quantidade)
    # A View analisa os números e cospe o JSON com os alertas visuais
    return ProdutoView.renderizar_baixa_estoque(dados_baixa)

@router.get("/alertas")
def buscar_alertas():
    criticos = ProdutoModel.listar_alertas_estoque()
    return ProdutoView.renderizar_relatorio_alertas(criticos)