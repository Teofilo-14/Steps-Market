from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa a função que cria todas as tabelas no banco de dados único
from src.models.database import inicializar_banco

# Importa todos os controladores (camada de Rotas) do sistema
from src.controllers.usuario_controller import router as usuario_router
from src.controllers.caixa_controller import router as caixa_router
from src.controllers.portaria_controller import router as portaria_router
from src.controllers.fila_controller import router as fila_router
from src.controllers.produto_controller import router as produto_router

# Inicializa o aplicativo FastAPI
app = FastAPI(title="Steps Market - Sistema Integrado de Automação Comercial")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== INICIALIZAÇÃO DO BANCO DE DADOS ======
inicializar_banco()

# ====== ACOPLAMENTO DE TODAS AS ROTAS (CONTROLLERS) ======
app.include_router(usuario_router)    # Gerenciamento de Usuários e Permissões
app.include_router(caixa_router)      # Controle de Caixa, Vendas e Cupons
app.include_router(portaria_router)   # Controle de Fluxo e Lotação Física
app.include_router(fila_router)       # Sistema de Senhas e Fila de Espera Virtual
app.include_router(produto_router)    # Controle de Estoque e Alertas de Produtos