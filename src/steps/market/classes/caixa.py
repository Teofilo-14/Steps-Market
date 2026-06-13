from datetime import datetime
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Banco SQLite local: Inicializa as tabelas essenciais se não existirem
with sqlite3.connect("caixa.db") as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS caixas (id INTEGER PRIMARY KEY, op TEXT, status TEXT, ini REAL, fin REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, valor REAL, m_pago TEXT)")

class CaixaIn(BaseModel): op: str; saldo: float
class VendaIn(BaseModel): valor: float; metodo: str # 'dinheiro', 'pix', 'cartao'

def obter_caixa_aberto():
    with sqlite3.connect("caixa.db") as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM caixas WHERE status = 'aberto'").fetchone()

@app.post("/api/caixa/abrir")
def abrir(p: CaixaIn):
    if obter_caixa_aberto(): raise HTTPException(400, "Já existe um caixa aberto.")
    with sqlite3.connect("caixa.db") as conn:
        conn.execute("INSERT INTO caixas (op, status, ini) VALUES (?, 'aberto', ?)", (p.op, p.saldo))
    return {"status": "Caixa aberto"}

@app.post("/api/caixa/venda")
def venda(p: VendaIn):
    # CRITÉRIO: Rejeita venda se o caixa estiver fechado
    if not obter_caixa_aberto(): raise HTTPException(400, "Operação Negada: Caixa FECHADO.")
    if p.metodo not in ['dinheiro', 'pix', 'cartao']: raise HTTPException(400, "Método inválido.")
    
    with sqlite3.connect("caixa.db") as conn:
        cursor = conn.execute("INSERT INTO vendas (valor, m_pago) VALUES (?, ?)", (p.valor, p.metodo))
        v_id = cursor.lastrowid
    
    # CRITÉRIO: Emite o recibo digital automático
    return {
        "mensagem": "Venda concluída",
        "recibo": {"cupom": f"NFCe-{v_id:04d}", "total": p.valor, "pago_via": p.metodo.upper(), "data": str(datetime.now())}
    }

@app.post("/api/caixa/fechar")
def fechar(p: CaixaIn): # Reaproveita o modelo CaixaIn (saldo informado)
    caixa = obter_caixa_aberto()
    if not caixa: raise HTTPException(400, "Nenhum caixa aberto.")
    
    with sqlite3.connect("caixa.db") as conn:
        vendas_dinheiro = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM vendas WHERE m_pago = 'dinheiro'").fetchone()[0]
        conn.execute("UPDATE caixas SET status = 'fechado', fin = ? WHERE id = ?", (p.saldo, caixa["id"]))
        conn.execute("DELETE FROM vendas") # Limpa as vendas para o próximo ciclo
        
    esperado = caixa["ini"] + vendas_dinheiro
    diferenca = p.saldo - esperado
    return {
        "status": "Caixa fechado",
        "auditoria": "Perfeito" if diferenca == 0 else f"Diferença de R$ {diferenca:.2f} (Furo/Sobra)"
    }
