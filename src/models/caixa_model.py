from fastapi import HTTPException
from pydantic import BaseModel
from src.models.database import get_db_connection

# 1. Schemas do Pydantic (Dados de Entrada)
class CaixaIn(BaseModel): 
    op: str
    saldo: float

class VendaIn(BaseModel): 
    valor: float
    metodo: str # 'dinheiro', 'pix', 'cartao'


# 2. Lógica de Negócio e Consultas ao Banco (Model)
class CaixaModel:
    
    @staticmethod
    def obter_caixa_aberto():
        with get_db_connection() as conn:
            return conn.execute("SELECT * FROM caixas WHERE status = 'aberto'").fetchone()

    @classmethod
    def abrir_caixa(cls, p: CaixaIn):
        if cls.obter_caixa_aberto(): 
            raise HTTPException(400, "Já existe um caixa aberto.")
        with get_db_connection() as conn:
            conn.execute("INSERT INTO caixas (op, status, ini) VALUES (?, 'aberto', ?)", (p.op, p.saldo))

    @classmethod
    def registrar_venda(cls, p: VendaIn) -> int:
        if not cls.obter_caixa_aberto(): 
            raise HTTPException(400, "Operação Negada: Caixa FECHADO.")
        if p.metodo not in ['dinheiro', 'pix', 'cartao']: 
            raise HTTPException(400, "Método inválido.")
        
        with get_db_connection() as conn:
            cursor = conn.execute("INSERT INTO vendas (valor, m_pago) VALUES (?, ?)", (p.valor, p.metodo))
            v_id = cursor.lastrowid # Pega o ID gerado automaticamente pelo banco
        
        return v_id # Retorna o ID puro (A View cuidará de formatar o recibo)

    @classmethod
    def fechar_caixa(cls, p: CaixaIn) -> str:
        caixa = cls.obter_caixa_aberto()
        if not caixa: 
            raise HTTPException(400, "Nenhum caixa aberto.")
        
        with get_db_connection() as conn:
            # Busca o total vendido em dinheiro
            vendas_dinheiro = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM vendas WHERE m_pago = 'dinheiro'").fetchone()[0]
            # Atualiza o status do caixa atual para fechado
            conn.execute("UPDATE caixas SET status = 'fechado', fin = ? WHERE id = ?", (p.saldo, caixa["id"]))
            # Limpa a tabela temporária de vendas para o próximo caixa
            conn.execute("DELETE FROM vendas")
            
        esperado = caixa["ini"] + vendas_dinheiro
        diferenca = p.saldo - esperado
        
        return "Perfeito" if diferenca == 0 else f"Diferença de R$ {diferenca:.2f} (Furo/Sobra)"