import sys
import os
import time
import webbrowser
import multiprocessing
import socket
import urllib.request

# Redireciona saídas em modo sem janela para não travar o Uvicorn
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
if sys.stdin is None:
    sys.stdin = open(os.devnull, "r")

def testar_servidor_online(porta=9000):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/status", timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False

def porta_esta_em_uso(porta=9000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', porta)) == 0

def aguardar_e_abrir_navegador(porta=9000):
    url = f"http://127.0.0.1:{porta}"
    # Tenta verificar se a API está online por até 15 segundos antes de abrir
    for _ in range(30):
        time.sleep(0.5)
        if testar_servidor_online(porta):
            webbrowser.open(url)
            return
    webbrowser.open(url)

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # 1. Se o AutoVision já estiver ativo na memória, abre a tela e sai sem criar backup duplicado
    if testar_servidor_online(9000):
        webbrowser.open("http://127.0.0.1:9000")
        sys.exit(0)

    # 2. Se a porta 9000 estiver presa por um processo fantasma/travado, encerra o zumbi
    if porta_esta_em_uso(9000):
        os.system("taskkill /f /im AutoVision.exe >nul 2>&1")
        time.sleep(1)

    # 3. Dispara a thread que aguarda o servidor ficar pronto de verdade
    import threading
    threading.Thread(target=aguardar_e_abrir_navegador, args=(9000,), daemon=True).start()

    # 4. Inicia o servidor FastAPI com Uvicorn
    import uvicorn
    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=9000, log_config=None)