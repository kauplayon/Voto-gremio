# Vota Grêmio

Sistema de votação estudantil com urna por número de candidato, cadastro de chapas/logos, cadastro individual de candidatos e apuração por pessoa. Feito com Flask e JSON.

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

## Armazenamento no Render
Configure um Persistent Disk montado em `/var/data` e a variável `DATA_DIR=/var/data`. Isso preserva o JSON e as imagens entre deploys. Se não houver disco persistente, arquivos locais podem ser perdidos ao reiniciar ou publicar uma nova versão.

## Migração
Na primeira execução com o novo código, os antigos grêmios são convertidos em chapas. Os totais antigos ficam preservados em uma seção separada, pois não é possível atribuí-los retroativamente a candidatos individuais. Os votos da nova eleição começam em zero; os nomes de eleitores já usados continuam bloqueados até que o responsável zere a votação.

## Limitações importantes
A verificação por nome não comprova a identidade do eleitor e pode ser contornada por outra pessoa. Este projeto é um protótipo; uma eleição oficial requer identificação validada, regras de auditoria, proteção de dados e testes de segurança.
