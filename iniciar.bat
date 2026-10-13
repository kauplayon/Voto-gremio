@echo off
title Vota Gremio
cd /d "%~dp0"
echo ========================================
echo          VOTA GREMIO - INICIALIZADOR
echo ========================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python nao foi encontrado.
  echo Instale o Python 3 em https://www.python.org/downloads/windows/
  echo Durante a instalacao, marque "Add Python to PATH".
  echo.
  pause
  exit /b 1
)
echo Verificando as dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERRO ao instalar as dependencias. Confira sua conexao com a internet.
  pause
  exit /b 1
)
echo.
echo Iniciando o Vota Gremio...
echo Quando aparecer que o servidor esta rodando, abra http://127.0.0.1:5000 no navegador.
echo Para encerrar, feche esta janela ou pressione CTRL+C.
echo.
python app.py
echo.
echo O Vota Gremio foi encerrado.
pause
