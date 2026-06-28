from datetime import datetime
from fastapi import HTTPException
from src.models.database import get_db_connection

class PortariaModel:
    LIMITE_MAXIMO = 10  # Definido como regra de negócio do modelo

    @classmethod
    def obter_total_dentro(cls) -> int:
        with get_db_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM ocupacao WHERE status = 'dentro'").fetchone()[0]

    @classmethod
    def registrar_entrada(cls, cartao_id: str) -> str:
        if cls.obter_total_dentro() >= cls.LIMITE_MAXIMO:
            raise HTTPException(status_code=400, detail="Entrada negada: Limite de lotação atingido.")
            
        with get_db_connection() as conn:
            cliente = conn.execute("SELECT status FROM ocupacao WHERE cartao_id = ?", (cartao_id,)).fetchone()
            if cliente and cliente[0] == "dentro":
                raise HTTPException(status_code=400, detail="Este cartão já está registrado dentro.")

            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT OR REPLACE INTO ocupacao (cartao_id, status, entrado_em) VALUES (?, 'dentro', ?)",
                (cartao_id, agora)
            )
        return cartao_id

    @classmethod
    def registrar_saida(cls, cartao_id: str) -> str:
        with get_db_connection() as conn:
            cliente = conn.execute("SELECT status FROM ocupacao WHERE cartao_id = ?", (cartao_id,)).fetchone()
            if not cliente or cliente[0] != "dentro":
                raise HTTPException(status_code=400, detail="Este cartão não possui registro de entrada ativo.")

            conn.execute("UPDATE ocupacao SET status = 'saiu' WHERE cartao_id = ?", (cartao_id,))
        return cartao_id