import sys
import os
from pathlib import Path

def obter_diretorio_base() -> Path:
    """
    Retorna o diretório permanente onde o .exe está localizado.
    Em desenvolvimento, retorna a raiz do repositório.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def obter_diretorio_dist() -> Path:
    """
    Localiza a pasta com os arquivos do frontend compilados com proteção para
    todas as variações de empacotamento do PyInstaller (onefile, onedir, _internal).
    """
    candidatos = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            p_mei = Path(sys._MEIPASS)
            candidatos.extend([p_mei / "frontend" / "dist", p_mei / "dist"])
            
        exe_dir = Path(sys.executable).resolve().parent
        candidatos.extend([
            exe_dir / "_internal" / "frontend" / "dist",
            exe_dir / "_internal" / "dist",
            exe_dir / "frontend" / "dist",
            exe_dir / "dist"
        ])
    else:
        raiz = Path(__file__).resolve().parent.parent
        candidatos.extend([raiz / "frontend" / "dist", raiz / "dist"])

    for pasta in candidatos:
        if pasta.exists() and (pasta / "index.html").exists():
            return pasta

    return candidatos[0]

DIRETORIO_BASE = obter_diretorio_base()
CAMINHO_BANCO = DIRETORIO_BASE / 'oficina.db'
PASTA_BACKUPS = DIRETORIO_BASE / 'backups'