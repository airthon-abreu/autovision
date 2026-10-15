@echo off

:: O parametro /B roda os servidores no fundo, sem estourar janelas novas
start /B "" cmd /c ".\venv\Scripts\activate.bat && uvicorn backend.main:app --port 9000"

:: Dá 3 segundos para o Python estabilizar
timeout /t 3 /nobreak > NUL

:: Inicia o Vue também no fundo
start /B "" cmd /c "cd frontend && npm run dev"

:: Dá mais 3 segundos para o Node.js compilar a tela
timeout /t 3 /nobreak > NUL

:: Abre o navegador na porta exata que travamos
start http://localhost:5173