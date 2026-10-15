import sqlite3
from datetime import datetime
from backend.config import CAMINHO_BANCO, PASTA_BACKUPS

def fazer_backup_banco():
    """
    Realiza backup a quente e consistente utilizando a API oficial de backup do SQLite,
    evitando corrupção de páginas e compatível com modo WAL.
    """
    if not CAMINHO_BANCO.exists():
        return

    PASTA_BACKUPS.mkdir(parents=True, exist_ok=True)

    data_hoje = datetime.now().strftime('%Y%m%d')
    nome_backup = f"oficina_{data_hoje}.db.bak"
    caminho_destino = PASTA_BACKUPS / nome_backup

    if caminho_destino.exists():
        try:
            mtime_banco = CAMINHO_BANCO.stat().st_mtime
            mtime_backup = caminho_destino.stat().st_mtime
            if mtime_banco <= mtime_backup:
                return
        except Exception:
            pass

    try:
        # Backup online atômico e transacional nativo do SQLite
        with sqlite3.connect(str(CAMINHO_BANCO)) as src:
            with sqlite3.connect(str(caminho_destino)) as dst:
                src.backup(dst)
        
        print(f"[Segurança] Backup diário registrado com sucesso: {nome_backup}")

        # Retenção: Mantém os 20 backups mais recentes
        backups = sorted(PASTA_BACKUPS.glob("oficina_*.db.bak"), key=lambda p: p.stat().st_mtime)
        while len(backups) > 20:
            antigo = backups.pop(0)
            try:
                antigo.unlink()
            except Exception:
                pass
    except Exception as e:
        print(f"[Erro de Segurança] Falha ao criar backup: {e}")