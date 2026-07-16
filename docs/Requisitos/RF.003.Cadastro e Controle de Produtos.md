# Cadastro e Controle de Produtos  
**Como** Gestor do sistema.  
**Quero** Que o sistema processe, armazene e gerencie o cadastro de produtos do estoque.  
**Para** Manter o controle exato das mercadorias disponíveis para venda e receber alertas automáticos quando os itens estiverem acabando.  

# Critérios de Aceitação  
Validar e persistir no banco de dados o nome do produto, preço unitário positivo, quantidade em estoque e o limite mínimo para alerta de reposição.  
Permitir o cadastro de novos produtos (POST) e a atualização de seus dados cadastrais ou níveis de estoque (PUT/PATCH).  
Disparar uma resposta de erro (HTTP 400) caso tente-se cadastrar um produto com preço ou quantidade negativos, ou campos obrigatórios em branco.  
Retornar um alerta visual de estoque baixo (status ou mensagem) na consulta do produto sempre que a quantidade atual for menor ou igual ao estoque mínimo definido.  
Permitir a remoção lógica ou física do produto do catálogo (DELETE), desde que o mesmo não possua pendências no sistema.  
