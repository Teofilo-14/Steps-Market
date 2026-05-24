# Cadastro de Usuário  
**Como** Administrador do sistema.  
**Quero** Que o sistema processe e armazene virtualmente o cadastro de novos usuários e funcionários com diferentes níveis de permissão.  
**Para** Autenticar os usuários com segurança e controlar o acesso às funcionalidades do mercadinho.  

# Criterios de Aceitação
Validar e persistir no banco de dados o nome, e-mail único, senha criptografada e o tipo de perfil (ex: operador, gestor)  
Permitir a atualização dos dados cadastrais (PATCH/PUT) e validar se o usuário que solicita a alteração possui permissão para isso  
Rejeitar a criação de contas que utilizem um endereço de e-mail já cadastrado no sistema  
Disparar uma resposta de erro (HTTP 400) caso algum campo obrigatório seja enviado em branco ou com formato inválido  
