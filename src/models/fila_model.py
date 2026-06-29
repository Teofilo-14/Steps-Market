from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel
from .database import get_db_connection

class RequisicaoCliente(BaseModel):
    nome: str = None

class ClienteFila:
    def __init__(self, senha: int, nome: str, status: str, horario_gerado: str = None):
        self.senha = senha
        self.nome = nome
        self.status = status
        self.horario_gerado = horario_gerado or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class FilaModel:
    LIMITE_MAXIMO = 10
    senha_atual_painel = 0 # Estado controlado na memória do servidor

    @classmethod
    def obter_quantidade_dentro(cls) -> int:
        with get_db_connection() as conn:
            return conn.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'dentro'").fetchone()["total"]

    @classmethod
    def emitir_nova_senha(cls, nome_cliente: str = None) -> ClienteFila:
        with get_db_connection() as conn:
            if not nome_cliente:
                proximo = conn.execute("SELECT COALESCE(MAX(senha), 0) + 1 as proximo FROM gerenciamento_fila").fetchone()["proximo"]
                nome_cliente = f"Cliente-{proximo:03d}"

            cursor = conn.execute("INSERT INTO gerenciamento_fila (nome, status) VALUES (?, 'esperando')", (nome_cliente,))
            id_gerado = cursor.lastrowid
            return ClienteFila(senha=id_gerado, nome=nome_cliente, status="esperando")

    @classmethod
    def chamar_proximo_cliente(cls) -> ClienteFila:
        if cls.obter_quantidade_dentro() >= cls.LIMITE_MAXIMO:
            raise HTTPException(status_code=400, detail="Lotação esgotada no momento.")

        with get_db_connection() as conn:
            dados = conn.execute("SELECT * FROM gerenciamento_fila WHERE status = 'esperando' ORDER BY senha ASC LIMIT 1").fetchone()

            if not dados:
                raise HTTPException(status_code=404, detail="Nenhum cliente aguardando na fila.")

            cls.senha_atual_painel = dados["senha"]
            conn.execute("UPDATE gerenciamento_fila SET status = 'chamado' WHERE senha = ?", (cls.senha_atual_painel,))
            
            return ClienteFila(senha=dados["senha"], nome=dados["nome"], status="chamado", horario_gerado=dados["horario_gerado"])

    @classmethod
    def confirmar_entrada_cliente(cls):
        if cls.senha_atual_painel == 0:
            raise HTTPException(status_code=400, detail="Não há nenhuma senha activa no painel para confirmar.")

        with get_db_connection() as conn:
            conn.execute("UPDATE gerenciamento_fila SET status = 'dentro' WHERE senha = ?", (cls.senha_atual_painel,))
        cls.senha_atual_painel = 0

    @classmethod
    def registrar_saida_cliente(cls):
        with get_db_connection() as conn:
            dados = conn.execute("SELECT senha FROM gerenciamento_fila WHERE status = 'dentro' ORDER BY horario_gerado ASC LIMIT 1").fetchone()

            if not dados:
                raise HTTPException(status_code=404, detail="Não há clientes dentro do estabelecimento.")

            conn.execute("UPDATE gerenciamento_fila SET status = 'saiu' WHERE senha = ?", (dados["senha"],))

    @classmethod
    def buscar_dados_fila(cls) -> dict:
        with get_db_connection() as conn:
            total_fila = conn.execute("SELECT COUNT(*) as total FROM gerenciamento_fila WHERE status = 'esperando'").fetchone()["total"]
            return {
                "limite_maximo": cls.LIMITE_MAXIMO,
                "clientes_dentro": cls.obter_quantidade_dentro(),
                "clientes_na_fila": total_fila,
                "senha_no_painel": cls.senha_atual_painel if cls.senha_atual_painel > 0 else None
            }