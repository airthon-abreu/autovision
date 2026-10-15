@echo off
echo ===================================================
echo     ENCERRANDO O SISTEMA DA OFICINA...
echo ===================================================
echo.

echo [1/2] Desligando o Backend (Porta 9000)...
FOR /F "tokens=5" %%T IN ('netstat -ano ^| findstr :9000') DO (
    taskkill /F /PID %%T > NUL 2>&1
)

echo [2/2] Desligando o Frontend (Portas 5173/5174)...
FOR /F "tokens=5" %%T IN ('netstat -ano ^| findstr :5174') DO (
    taskkill /F /PID %%T > NUL 2>&1
)
FOR /F "tokens=5" %%T IN ('netstat -ano ^| findstr :5173') DO (
    taskkill /F /PID %%T > NUL 2>&1
)

echo.
echo Sistema encerrado com sucesso!
timeout /t 3 > NUL