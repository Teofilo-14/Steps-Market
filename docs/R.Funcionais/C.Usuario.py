from datetime import datetime
import sqlite3
import hashlib
import re
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()

# Inicializa a tabela de usuários com níveis de perfil
with sqlite3.connect("usuarios.db") as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY, nome TEXT, email TEXT UNIQUE, senha TEXT, perfil TEXT
        )
    """)

class UserIn(BaseModel): nome: str; email: str; senha: str; perfil: str # 'gestor' ou 'operador'
class UserUpdate(BaseModel): nome: str = None; email: str = None; senha: str = None

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def validar_campos(nome, email, senha, perfil=None):
    # CRITÉRIO: Erro 400 se campo obrigatório estiver em branco ou formato inválido
    if not nome or not email or not senha: raise HTTPException(400, "Campos não podem ser vazios.")
    if perfil and perfil not in ['gestor', 'operador']: raise HTTPException(400, "Perfil inválido.")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): raise HTTPException(400, "Formato de e-mail inválido.")

@app.post("/api/usuarios/cadastrar", status_code=201)
def cadastrar(p: UserIn):
    validar_campos(p.nome, p.email, p.senha, p.perfil)
    
    with sqlite3.connect("usuarios.db") as conn:
        # CRITÉRIO: Rejeita se o e-mail já estiver cadastrado
        existe = conn.execute("SELECT 1 FROM usuarios WHERE email = ?", (p.email,)).fetchone()
        if existe: raise HTTPException(400, "E-mail já cadastrado.")
        
        # CRITÉRIO: Persiste nome, e-mail único, senha criptografada e perfil
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha, perfil) VALUES (?, ?, ?, ?)",
            (p.nome, p.email, hash_senha(p.senha), p.perfil)
        )
    return {"status": "Usuário cadastrado com sucesso"}

@app.put("/api/usuarios/{user_id}")
def atualizar(user_id: int, p: UserUpdate, x_perfil_usuario: str = Header(None)):
    # CRITÉRIO: Valida se quem solicita a alteração possui a permissão (Apenas gestor pode alterar)
    if x_perfil_usuario != "gestor": 
        raise HTTPException(403, "Acesso negado: Apenas gestores podem atualizar cadastros.")
        
    with sqlite3.connect("usuarios.db") as conn:
        conn.row_factory = sqlite3.Row
        usuario = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        if not usuario: raise HTTPException(404, "Usuário não encontrado.")
        
        # Prepara os dados mantendo o antigo se o novo for enviado em branco
        nome = p.nome if p.nome else usuario["nome"]
        email = p.email if p.email else usuario["email"]
        senha = hash_senha(p.senha) if p.senha else usuario["senha"]
        
        validar_campos(nome, email, senha)
        
        # CRITÉRIO: Permite a atualização dos dados cadastrais
        conn.execute(
            "UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?",
            (nome, email, senha, user_id)
        )
    return {"status": "Cadastro atualizado"}