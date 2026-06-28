from fastapi import HTTPException
from pydantic import BaseModel
from src.models.database import get_db_connection

# Schema de Entrada do Pydantic
class ProdutoIn(BaseModel):
    nome: str
    preco: float
    quantidade: int
    estoque_minimo: int = 5

class ProdutoModel:

    @classmethod
    def cadastrar_produto(cls, p: ProdutoIn):
        if p.preco <= 0 or p.quantidade < 0:
            raise HTTPException(400, "Preço ou quantidade inválidos.")
            
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO produtos (nome, preco, quantidade, estoque_minimo) VALUES (?, ?, ?, ?)",
                (p.nome, p.preco, p.quantidade, p.estoque_minimo)
            )

    @classmethod
    def simular_venda_produto(cls, produto_id: int, qtd_vendida: int):
        """Baixa o estoque e avisa se o produto acabou ou está abaixo do mínimo."""
        with get_db_connection() as conn:
            prod = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
            
            if not prod:
                raise HTTPException(404, "Produto não encontrado.")
            if prod["quantidade"] < qtd_vendida:
                raise HTTPException(400, f"Estoque insuficiente. Disponível: {prod['quantidade']}")
                
            nova_qtd = prod["quantidade"] - qtd_vendida
            conn.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, produto_id))
            
            # Retorna o estado atual para a View decidir o alerta
            return {
                "nome": prod["nome"],
                "restante": nova_qtd,
                "minimo": prod["estoque_minimo"]
            }

    @classmethod
    def listar_alertas_estoque(cls) -> list:
        """Busca produtos que estão abaixo do limite mínimo."""
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM produtos WHERE quantidade <= estoque_minimo")
            return [dict(row) for row in cursor.fetchall()]