# Vota Grêmio

Aplicação de votação estudantil feita com Flask e arquivo JSON.

## Executar localmente
1. Instale o Python 3.
2. No terminal, dentro da pasta do projeto, execute: `pip install -r requirements.txt`
3. Defina uma senha de administrador (recomendado):
   - Windows PowerShell: `$env:ADMIN_PASSWORD="sua-senha"`
   - macOS/Linux: `export ADMIN_PASSWORD="sua-senha"`
4. Execute: `python app.py`
5. Abra `http://127.0.0.1:5000` no navegador.
6. Painel administrativo: `http://127.0.0.1:5000/admin`

A senha inicial, se não configurar ADMIN_PASSWORD, é `admin123` (troque antes de usar).

Os dados ficam em `votos.json`, criado automaticamente. Faça cópias de segurança.

## Limitações
Este é um protótipo para demonstração/testes. A identificação por nome não comprova a identidade do aluno: nomes podem ser repetidos ou usados por outra pessoa. O arquivo local também pode ser alterado por quem tiver acesso ao computador. Não use como sistema oficial sem validação, supervisão e medidas adicionais de segurança e privacidade.

## Hospedagem
O arquivo JSON pode ser apagado em reinicializações ou novos deploys em serviços de hospedagem. Para preservar votos online, será necessário configurar armazenamento persistente ou um banco de dados.
