from datetime import datetime
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="API Mercadinho - Banco de Dados Nativo SQLite")

# Configuração de CORS para permitir comunicação com o seu Front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== MODELO DE ENTRADA (Front-end) ======
class RequisicaoCliente(BaseModel):
    nome: str = None


# ====== CLASSE DE GERENCIAMENTO (SQLite) ======
class SistemaLotacaoSQLite:
    def __init__(self, limite: int = 10, nome_banco: str = "mercadinho.db"):
        self.limite = limite
        self.nome_banco = nome_banco
        self.senha_atual = 0
        self._criar_tabela_inicial()

    def _obter_conexao(self):
        """Abre uma conexão com o arquivo de banco de dados local"""
        # O sqlite3.Row permite acessar as colunas pelo nome (ex: cliente["nome"])
        conexao = sqlite3.connect(self.nome_banco)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _criar_tabela_inicial(self):
        """Cria a tabela no arquivo .db se ela ainda não existir"""
        db = self._obter_conexao()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gerenciamento_fila (
                senha INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                status TEXT CHECK(status IN ('esperando', 'chamado', 'dentro', 'saiu', 'cancelado')) DEFAULT 'esperando',
                horario_gerado TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        db.commit()
        cursor.close()
        db.close()

    def obter_total_dentro(self) -> int:
        db = self._obter_conexao()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'dentro'")
        total = cursor.fetchone()["total"]
        cursor.close()
        db.close()
        return total

    def gerar_senha(self, nome: str = None) -> dict:
        db = self._obter_conexao()
        cursor = db.cursor()
        
        if not nome:
            cursor.execute("SELECT COALESCE(MAX(senha), 0) + 1 as proximo FROM gerenciamento_fila")
            proximo_id = cursor.fetchone()["proximo"]
            nome = f"Cliente-{proximo_id:03d}"

        cursor.execute("INSERT INTO gerenciamento_fila (nome, status) VALUES (?, 'esperando')", (nome,))
        db.commit()
        
        senha_gerada = cursor.lastrowid
        cursor.close()
        db.close()
        
        return {"senha": senha_gerada, "nome": nome, "status": "esperando"}

    def chamar(self) -> dict:
        dentro = self.obter_total_dentro()
        if dentro >= self.limite:
            raise HTTPException(status_code=400, detail=f"⚠️ LOTAÇÃO CHEIA! ({dentro}/{self.limite})")

        db = self._obter_conexao()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM gerenciamento_fila WHERE status = 'esperando' ORDER BY senha ASC LIMIT 1")
        cliente = cursor.fetchone()

        if not cliente:
            cursor.close()
            db.close()
            raise HTTPException(status_code=404, detail="📋 Fila vazia!")

        self.senha_atual = cliente["senha"]
        cursor.execute("UPDATE gerenciamento_fila SET status = 'chamado' WHERE senha = ?", (self.senha_atual,))
        db.commit()
        
        dados_cliente = {"senha": cliente["senha"], "nome": cliente["nome"], "status": "chamado"}
        cursor.close()
        db.close()
        return dados_cliente

    def confirmar_entrada(self) -> dict:
        if self.senha_atual == 0:
            raise HTTPException(status_code=400, detail="❌ Nenhuma senha foi chamada recentemente!")

        db = self._obter_conexao()
        cursor = db.cursor()
        cursor.execute("UPDATE gerenciamento_fila SET status = 'dentro' WHERE senha = ?", (self.senha_atual,))
        db.commit()
        
        self.senha_atual = 0
        cursor.close()
        db.close()
        
        return {"mensagem": "Entrada confirmada com sucesso!", "total_dentro": self.obter_total_dentro()}

    def registrar_saida(self) -> dict:
        db = self._obter_conexao()
        cursor = db.cursor()
        
        cursor.execute("SELECT senha FROM gerenciamento_fila WHERE status = 'dentro' ORDER BY horario_gerado ASC LIMIT 1")
        cliente = cursor.fetchone()

        if not cliente:
            cursor.close()
            db.close()
            raise HTTPException(status_code=404, detail="❌ Nenhum cliente dentro!")

        cursor.execute("UPDATE gerenciamento_fila SET status = 'saiu' WHERE senha = ?", (cliente["senha"],))
        db.commit()
        
        id_saida = cliente["senha"]
        cursor.close()
        db.close()
        
        return {"mensagem": f"Saída OK - Senha {id_saida:03d}", "total_dentro": self.obter_total_dentro()}

    def cancelar(self) -> dict:
        db = self._obter_conexao()
        cursor = db.cursor()
        
        cursor.execute("SELECT senha FROM gerenciamento_fila WHERE status = 'esperando' ORDER BY senha DESC LIMIT 1")
        cliente = cursor.fetchone()

        if not cliente:
            cursor.close()
            db.close()
            raise HTTPException(status_code=404, detail="📋 Nenhuma senha esperando para cancelar!")

        cursor.execute("UPDATE gerenciamento_fila SET status = 'cancelado' WHERE senha = ?", (cliente["senha"],))
        db.commit()
        
        id_cancelado = cliente["senha"]
        cursor.close()
        db.close()
        return {"mensagem": f"❌ Senha {id_cancelado:03d} cancelada!"}

    def obter_dados_dashboard(self) -> dict:
        db = self._obter_conexao()
        cursor = db.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'esperando'")
        total_fila = cursor.fetchone()["total"]
        
        cursor.close()
        db.close()
        
        return {
            "limite_maximo": self.limite,
            "clientes_dentro": self.obter_total_dentro(),
            "clientes_na_fila": total_fila,
            "senha_no_painel": self.senha_atual if self.senha_atual > 0 else None
        }


# Instancia o sistema com limite de 10 pessoas
sistema = SistemaLotacaoSQLite(limite=10)


# ====== ROTAS HTTP PARA O FRONT-END ======

@app.get("/api/dashboard")
def api_dashboard():
    return sistema.obter_dados_dashboard()

@app.post("/api/senha/gerar", status_code=201)
def api_gerar_senha(payload: RequisicaoCliente):
    return sistema.gerar_senha(payload.nome)

@app.post("/api/painel/chamar")
def api_chamar():
    return sistema.chamar()

@app.put("/api/painel/confirmar")
def api_confirmar():
    return sistema.confirmar_entrada()

@app.put("/api/clientes/registrar-saida")
def api_saida():
    return sistema.registrar_saida()

@app.put("/api/senha/cancelar")
def api_cancelar():
    return sistema.cancelar()
