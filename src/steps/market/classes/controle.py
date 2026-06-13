from datetime import datetime
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="API Mercadinho - Arquitetura POO com SQLite")

# Permite que o seu Front-end (mesmo rodando em outra porta/servidor) acesse o Back-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== MODELO DE ENTRADA DO FRONT-END (Pydantic) ======
class RequisicaoCliente(BaseModel):
    nome: str = None


# ====== CLASSES DO DOMÍNIO (POO) ======

class ClienteFila:
    """Classe que representa a entidade de um cliente no sistema"""
    def __init__(self, senha: int, nome: str, status: str, horario_gerado: str = None):
        self.senha = senha
        self.nome = nome
        self.status = status
        self.horario_gerado = horario_gerado or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def para_dicionario(self):
        """Converte o objeto em dicionário para o FastAPI enviar como JSON ao Front-end"""
        return {
            "senha": self.senha,
            "nome": self.nome,
            "status": self.status,
            "horario_gerado": self.horario_gerado
        }


class GerenciadorFila:
    """Classe responsável por gerenciar as regras de negócio e persistência no SQLite"""
    def __init__(self, limite_maximo: int = 10, nome_banco: str = "mercadinho.db"):
        self.limite_maximo = limite_maximo
        self.nome_banco = nome_banco
        self.senha_atual_painel = 0
        self._criar_tabela_inicial()

    def _conectar(self):
        """Método interno para obter conexão com o SQLite local"""
        conexao = sqlite3.connect(self.nome_banco)
        # Permite acessar os resultados do banco por nome de coluna (ex: dados["nome"])
        conexao.row_factory = sqlite3.Row
        return conexao

    def _criar_tabela_inicial(self):
        """Cria a estrutura da tabela automaticamente se não existir no arquivo local"""
        conexao = self._conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gerenciamento_fila (
                senha INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                status TEXT CHECK(status IN ('esperando', 'chamado', 'dentro', 'saiu', 'cancelado')) DEFAULT 'esperando',
                horario_gerado TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conexao.commit()
        cursor.close()
        conexao.close()

    def obter_quantidade_dentro(self) -> int:
        conexao = self._conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'dentro'")
        total = cursor.fetchone()["total"]
        cursor.close()
        conexao.close()
        return total

    def emitir_nova_senha(self, nome_cliente: str = None) -> ClienteFila:
        conexao = self._conectar()
        cursor = conexao.cursor()
        
        if not nome_cliente:
            cursor.execute("SELECT COALESCE(MAX(senha), 0) + 1 as proximo FROM gerenciamento_fila")
            proximo_id = cursor.fetchone()["proximo"]
            nome_cliente = f"Cliente-{proximo_id:03d}"

        cursor.execute("INSERT INTO gerenciamento_fila (nome, status) VALUES (?, 'esperando')", (nome_cliente,))
        conexao.commit()
        
        id_gerado = cursor.lastrowid
        cursor.close()
        conexao.close()
        
        return ClienteFila(senha=id_gerado, nome=nome_cliente, status="esperando")

    def chamar_proximo_cliente(self) -> ClienteFila:
        if self.obter_quantidade_dentro() >= self.limite_maximo:
            raise HTTPException(status_code=400, detail="Lotação esgotada no momento.")

        conexao = self._conectar()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT * FROM gerenciamento_fila WHERE status = 'esperando' ORDER BY senha ASC LIMIT 1")
        dados = cursor.fetchone()

        if not dados:
            cursor.close()
            conexao.close()
            raise HTTPException(status_code=404, detail="Nenhum cliente aguardando na fila.")

        self.senha_atual_painel = dados["senha"]
        cursor.execute("UPDATE gerenciamento_fila SET status = 'chamado' WHERE senha = ?", (self.senha_atual_painel,))
        conexao.commit()
        
        cliente = ClienteFila(senha=dados["senha"], nome=dados["nome"], status="chamado", horario_gerado=dados["horario_gerado"])
        cursor.close()
        conexao.close()
        
        return cliente

    def confirmar_entrada_cliente(self) -> bool:
        if self.senha_atual_painel == 0:
            raise HTTPException(status_code=400, detail="Não há nenhuma senha ativa no painel para confirmar.")

        conexao = self._conectar()
        cursor = conexao.cursor()
        cursor.execute("UPDATE gerenciamento_fila SET status = 'dentro' WHERE senha = ?", (self.senha_atual_painel,))
        conexao.commit()
        
        self.senha_atual_painel = 0
        cursor.close()
        conexao.close()
        return True

    def registrar_saida_cliente(self) -> bool:
        conexao = self._conectar()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT senha FROM gerenciamento_fila WHERE status = 'dentro' ORDER BY horario_gerado ASC LIMIT 1")
        dados = cursor.fetchone()

        if not dados:
            cursor.close()
            conexao.close()
            raise HTTPException(status_code=404, detail="Não há clientes dentro do estabelecimento.")

        cursor.execute("UPDATE gerenciamento_fila SET status = 'saiu' WHERE senha = ?", (dados["senha"],))
        conexao.commit()
        
        cursor.close()
        conexao.close()
        return True

    def buscar_dados_dashboard(self) -> dict:
        conexao = self._conectar()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'esperando'")
        total_fila = cursor.fetchone()["total"]
        
        cursor.close()
        conexao.close()
        
        return {
            "limite_maximo": self.limite_maximo,
            "clientes_dentro": self.obter_quantidade_dentro(),
            "clientes_na_fila": total_fila,
            "senha_no_painel": self.senha_atual_painel if self.senha_atual_painel > 0 else None
        }


# Instanciação do objeto gerenciador (Limite de 10 pessoas)
gerenciador = GerenciadorFila(limite_maximo=10)


# ====== ROTAS HTTP QUE O FRONT-END IRÁ CONSUMIR ======

@app.get("/api/dashboard")
def rota_dashboard():
    return gerenciador.buscar_dados_dashboard()

@app.post("/api/senha/gerar", status_code=201)
def rota_gerar_senha(payload: RequisicaoCliente):
    novo_cliente = gerenciador.emitir_nova_senha(payload.nome)
    return novo_cliente.para_dicionario()

@app.post("/api/painel/chamar")
def rota_chamar():
    cliente_chamado = gerenciador.chamar_proximo_cliente()
    return cliente_chamado.para_dicionario()

@app.put("/api/painel/confirmar")
def rota_confirmar():
    gerenciador.confirmar_entrada_cliente()
    return {"status": "sucesso", "mensagem": "Entrada validada com sucesso."}

@app.put("/api/clientes/saida")
def rota_saida():
    gerenciador.registrar_saida_cliente()
    return {"status": "sucesso", "mensagem": "Saída processada, vaga liberada."}
