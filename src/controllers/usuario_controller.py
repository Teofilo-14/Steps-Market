from fastapi import APIRouter, HTTPException, Header
from src.models.usuario_model import UserIn, UserUpdate, UsuarioModel
from src.views.usuario_view import UsuarioView

router = APIRouter(prefix="/api/usuarios")

@router.post("/cadastrar", status_code=201)
def cadastrar(p: UserIn):
    UsuarioModel.cadastrar_usuario(p)
    # Chama a View para gerar a resposta visual/JSON
    return UsuarioView.resposta_sucesso("Usuário cadastrado com sucesso")

@router.put("/{user_id}")
def atualizar(user_id: int, p: UserUpdate, x_perfil_usuario: str = Header(None)):
    if x_perfil_usuario != "gestor": 
        raise HTTPException(403, "Acesso negado: Apenas gestores podem atualizar cadastros.")
        
    UsuarioModel.atualizar_usuario(user_id, p)
    return UsuarioView.resposta_sucesso("Cadastro atualizado")