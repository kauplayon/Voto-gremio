# Vota Grêmio

Sistema de votação estudantil com urna por número de candidato, cadastro de chapas/logos, cadastro individual de candidatos e apuração por pessoa. Feito com Flask e PostgreSQL externo (ou JSON local para desenvolvimento).

## Executar localmente
1. Instale o Python 3.
2. Execute `pip install -r requirements.txt`.
3. Configure `ADMIN_PASSWORD` (recomendado) e `SECRET_KEY`.
4. Execute `python app.py`.
5. Abra `http://127.0.0.1:5000`; painel: `http://127.0.0.1:5000/admin`.

Se `ADMIN_PASSWORD` não estiver configurada, a senha inicial é `admin123`. Troque-a antes de usar.

## Como configurar a eleição
1. Entre no painel administrativo.
2. Cadastre cada chapa e envie o logo.
3. Cadastre cada candidato com número único, nome completo, chapa e, opcionalmente, foto.
4. Abra a votação. O eleitor informa seu nome e o número do candidato, confere nome/chapa/logo e confirma.
5. A apuração mostra os votos de cada candidato separadamente e pode ser exportada em CSV.

## Armazenamento persistente no Render grátis

O Render gratuito usa um sistema de arquivos temporário. Para manter chapas, candidatos, cargos, votos, nomes de eleitores, fotos e logos entre reinicializações, configure um PostgreSQL externo.

1. Crie um projeto PostgreSQL no Supabase.
2. No painel do Supabase, abra **Connect** e copie a connection string do **Session pooler** (recomendado para conexão IPv4), substituindo o marcador da senha pela senha do banco.
3. No painel do Render, abra o serviço do Vota Grêmio e entre em **Environment**.
4. Adicione a variável `DATABASE_URL` com a connection string completa. Não compartilhe essa URL: ela contém credenciais privadas.
5. Salve e faça o deploy da versão mais recente.
6. Na primeira inicialização, o app cria as tabelas necessárias. O estado da eleição e as imagens passam a ser guardados no banco.
7. Faça um teste cadastrando uma chapa e um candidato; reinicie o serviço e confirme que continuam lá.

Se `DATABASE_URL` não estiver definida, o app usa JSON e arquivos locais para desenvolvimento. O banco externo precisa estar ativo e acessível para o site salvar ou ler dados.

## Migração
Na primeira execução com o novo código, os antigos grêmios são convertidos em chapas. Os totais antigos ficam preservados em uma seção separada, pois não é possível atribuí-los retroativamente a candidatos individuais. Os votos da nova eleição começam em zero; os nomes de eleitores já usados continuam bloqueados até que o responsável zere a votação.

## Limitações importantes
A verificação por nome não comprova a identidade do eleitor e pode ser contornada por outra pessoa. Este projeto é um protótipo; uma eleição oficial requer identificação validada, regras de auditoria, proteção de dados e testes de segurança.
