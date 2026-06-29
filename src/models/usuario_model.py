import hashlib
import re
from fastapi import HTTPException
from pydantic import BaseModel
from .database import get_db_connection

class UserIn(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str

class UserUpdate(BaseModel):
    nome: str = None
    email: str = None
    senha: str = None

class UsuarioModel:
    @staticmethod
    def hash_senha(senha: str) -> str:
        return hashlib.sha256(senha.encode()).hexdigest()

    @staticmethod
    def validar_campos(nome, email, senha, perfil=None):
        if not nome or not email or not senha: 
            raise HTTPException(400, "Campos não podem ser vazios.")
        if perfil and perfil not in ['gestor', 'operador']: 
            raise HTTPException(400, "Perfil inválido.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
            raise HTTPException(400, "Formato de e-mail inválido.")

    @classmethod
    def cadastrar_usuario(cls, p: UserIn):
        cls.validar_campos(p.nome, p.email, p.senha, p.perfil)
        
        with get_db_connection() as conn:
            existe = conn.execute("SELECT 1 FROM usuarios WHERE email = ?", (p.email,)).fetchone()
            if existe: 
                raise HTTPException(400, "E-mail já cadastrado.")
            
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha, perfil) VALUES (?, ?, ?, ?)",
                (p.nome, p.email, cls.hash_senha(p.senha), p.perfil)
            )

    @classmethod
    def atualizar_usuario(cls, user_id: int, p: UserUpdate):
        with get_db_connection() as conn:
            usuario = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not usuario: 
                raise HTTPException(404, "Usuário não encontrado.")
            
            nome = p.nome if p.nome else usuario["nome"]
            email = p.email if p.email else usuario["email"]
            senha = cls.hash_senha(p.senha) if p.senha else usuario["senha"]
            
            cls.validar_campos(nome, email, senha)
            
            conn.execute(
                "UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?",
                (nome, email, senha, user_id)
            )