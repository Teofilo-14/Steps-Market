from datetime import datetime
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Controle de Acesso Orientado a Objetos")

# ====== CLASSE DO DOMÍNIO (POO) ======
class ControladorAcesso:
    def __init__(self, limite_maximo: int = 10, nome_banco: str = "portaria.db"):
        self.limite_maximo = limite_maximo
        self.nome_banco = nome_banco
        self._inicializar_banco()

    def _conectar(self):
        """Abre conexão com o banco SQLite"""
        return sqlite3.connect(self.nome_banco)

    def _inicializar_banco(self):
        """Cria a tabela inicial de ocupação se não existir"""
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ocupacao (
                    cartao_id TEXT PRIMARY KEY, status TEXT, entrado_em TEXT
                )
            """)

    def obter_total_dentro(self) -> int:
        """Calcula a quantidade de pessoas atualmente dentro do local"""
        with self._conectar() as conn:
            return conn.execute("SELECT COUNT(*) FROM ocupacao WHERE status = 'dentro'").fetchone()[0]

    def registrar_entrada(self, cartao_id: str) -> dict:
        """Regra de negócio para validar e permitir a entrada via cartão/QR Code"""
        # CRITÉRIO: Impede entrada se atingir o limite (exige uma saída prévia)
        if self.obter_total_dentro() >= self.limite_maximo:
            raise HTTPException(status_code=400, detail="Entrada negada: Limite de lotação atingido.")
            
        with self._conectar() as conn:
            cliente = conn.execute("SELECT status FROM ocupacao WHERE cartao_id = ?", (cartao_id,)).fetchone()
            if cliente and cliente[0] == "dentro":
                raise HTTPException(status_code=400, detail="Este cartão já está registrado dentro.")

            # CRITÉRIO: Registra a entrada com data e hora atual
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT OR REPLACE INTO ocupacao (cartao_id, status, entrado_em) VALUES (?, 'dentro', ?)",
                (cartao_id, agora)
            )
        return {"status": "Entrada liberada", "cartao": cartao_id}

    def registrar_saida(self, cartao_id: str) -> dict:
        """Regra de negócio para registrar a saída e liberar vaga instantaneamente"""
        with self._conectar() as conn:
            cliente = conn.execute("SELECT status FROM ocupacao WHERE cartao_id = ?", (cartao_id,)).fetchone()
            if not cliente or cliente[0] != "dentro":
                raise HTTPException(status_code=400, detail="Este cartão não possui registro de entrada ativo.")

            # CRITÉRIO: Registra a saída e atualiza o total instantaneamente
            conn.execute("UPDATE ocupacao SET status = 'saiu' WHERE cartao_id = ?", (cartao_id,))
            
        return {"status": "Saída processada, vaga liberada", "cartao": cartao_id}

    def gerar_dados_dashboard(self) -> dict:
        """Retorna os dados consolidados para o painel em tempo real"""
        dentro = self.obter_total_dentro()
        return {
            "clientes_dentro": dentro,
            "vagas_disponiveis": max(0, self.limite_maximo - dentro),
            "status_estabelecimento": "LOTADO" if dentro >= self.limite_maximo else "LIBERADO"
        }


# Instanciação global da classe (Definindo o limite de 10 pessoas)
controlador = ControladorAcesso(limite_maximo=10)


# ====== ROTAS HTTP PARA O FRONT-END ======

@app.get("/api/portaria/dashboard")
def rota_dashboard():
    # Aciona o método da classe para renderizar o painel segundo a segundo
    return controlador.gerar_dados_dashboard()

@app.post("/api/portaria/entrada/{cartao_id}")
def rota_entrada(cartao_id: str):
    # Aciona o método da classe focado em entrada
    return controlador.registrar_entrada(cartao_id)

@app.post("/api/portaria/saida/{cartao_id}")
def rota_saida(cartao_id: str):
    # Aciona o método da classe focado em saída
    return controlador.registrar_saida(cartao_id)
