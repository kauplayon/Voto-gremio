# Vota Grêmio

Sistema de votação estudantil com cadastro de chapas/logos, candidatos/cargos/fotos, votação por número, apuração e exportação CSV.

## Usar no Windows (computador local)

Esta é a opção recomendada para usar a votação em apenas um computador. Os dados são salvos no arquivo local `votos.json`, e as imagens ficam na pasta `uploads`. Eles permanecem no computador mesmo depois de fechar o navegador ou reiniciar o PC, desde que esses arquivos e pastas não sejam apagados.

1. Instale o Python 3 para Windows: https://www.python.org/downloads/windows/ . Durante a instalação, marque **Add Python to PATH**.
2. Baixe o projeto pelo botão **Code > Download ZIP** no GitHub e extraia a pasta para um local fixo do computador.
3. Dê dois cliques em `iniciar.bat`. Na primeira execução, ele instala as dependências; é necessária conexão com a internet para essa etapa.
4. Quando o servidor iniciar, abra `http://127.0.0.1:5000` no navegador do mesmo computador.
5. Para administrar a eleição, abra `http://127.0.0.1:5000/admin`.
6. Para encerrar, volte à janela preta do `iniciar.bat` e pressione `Ctrl+C`.

**Importante:** não mova nem apague `votos.json` ou a pasta `uploads` depois de cadastrar candidatos ou registrar votos. Para fazer backup, feche o sistema e copie o arquivo `votos.json` e a pasta `uploads` para outro local seguro. Para continuar usando os dados, inicie sempre o projeto pela mesma pasta.

Se `DATABASE_URL` estiver configurada nas variáveis de ambiente do Windows, o programa tentará usar o banco externo. Para o modo local, não configure essa variável; o programa usará `votos.json` e a pasta `uploads`.

## Senhas

Se `ADMIN_PASSWORD` não estiver configurada, a senha inicial é `admin123`. Altere-a antes de usar, definindo a variável de ambiente `ADMIN_PASSWORD`. Também é recomendado definir `SECRET_KEY`.

## Configurar a eleição

1. Entre no painel administrativo.
2. Cadastre cada chapa e envie o logo.
3. Cadastre cada candidato com número único, nome completo, cargo, chapa e, opcionalmente, foto.
4. Abra a votação. O eleitor informa o nome e o número do candidato, confere os dados e confirma.
5. Consulte os resultados no painel e exporte em CSV se necessário.

## Observação sobre o modo local

O sistema fica acessível em `127.0.0.1` somente no próprio computador. Os alunos precisam votar nesse computador, um por vez. O modo local não sincroniza votos com o site hospedado no Render.

A verificação por nome não comprova a identidade do eleitor. Este projeto é um protótipo; uma eleição oficial requer identificação validada, regras de auditoria, proteção de dados e testes de segurança.
