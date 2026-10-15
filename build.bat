@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================================
echo   COMPILAÇÃO OFICIAL - AUTOVISION (COM ÍCONE EMBUTIDO)
echo ========================================================

call :limpar_pastas

echo.
echo [1/4] Verificando e ativando ambiente virtual Python...
if not exist "venv\Scripts\activate.bat" (
    echo [*] Pasta venv nao encontrada. Criando ambiente virtual...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERRO] Nao foi possivel criar a venv.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Garantindo pacotes necessarios (openpyxl, pyinstaller, pillow, etc)...
python -m pip install --quiet openpyxl pyinstaller fastapi uvicorn pydantic pillow

echo.
echo [2/4] Gerando icone nativo do Windows em alta resolucao...
python -c "from PIL import Image; import os; p = 'frontend/public/logo.png' if os.path.exists('frontend/public/logo.png') else ('icone.png' if os.path.exists('icone.png') else None); (Image.open(p).save('icone.ico', format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]), print('    [OK] Arquivo icone.ico gerado com sucesso a partir de ' + p)) if p else print('    [AVISO] Nenhuma imagem base encontrada.')"

set ICON_FLAG=
if exist "icone.ico" (
    set ICON_FLAG=--icon "icone.ico"
)

echo.
echo [3/4] Compilando Frontend (AutoVision UI)...
cd frontend
if not exist "node_modules\" (
    echo [*] Instalando dependencias do frontend...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao rodar npm install!
        cd ..
        pause
        exit /b %errorlevel%
    )
)

call npm run build
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao rodar build. Tentando reinstalar dependencias...
    call npm install
    call npm run build
    if %errorlevel% neq 0 (
        echo [ERRO] Falha definitiva ao compilar o frontend!
        cd ..
        pause
        exit /b %errorlevel%
    )
)
cd ..

echo.
echo [4/4] Gerando executavel portatil AutoVision.exe...
python -m PyInstaller --noconfirm --onedir --windowed ^
    --name "AutoVision" ^
    %ICON_FLAG% ^
    --add-data "frontend/dist;frontend/dist" ^
    --collect-all "openpyxl" ^
    --hidden-import "uvicorn" ^
    run.py

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao gerar o executavel AutoVision!
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo   AUTOVISION COMPILADO COM SUCESSO!
echo   Pasta de saída: dist\AutoVision\
echo ========================================================
pause
exit /b 0

:limpar_pastas
echo.
echo [*] Executando rotina de limpeza previa...
taskkill /f /im AutoVision.exe >nul 2>&1
timeout /t 1 /nobreak >nul

if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "frontend\dist" rmdir /s /q "frontend\dist" 2>nul
echo [*] Limpeza concluida com sucesso!
exit /b 0