import sqlite3
import calendar
from datetime import datetime
from contextlib import contextmanager
from backend.config import CAMINHO_BANCO

@contextmanager
def obter_conexao():
    """
    Gerenciador de contexto com WAL ativado, timeout resiliente e fechamento garantido.
    """
    conexao = sqlite3.connect(str(CAMINHO_BANCO), timeout=30.0)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA journal_mode=WAL;")
    conexao.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()

def criar_tabelas():
    with obter_conexao() as conexao:
        cursor = conexao.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boletos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distribuidora TEXT NOT NULL,
                numero_nota TEXT,
                valor_parcela REAL NOT NULL,
                data_emissao DATE,
                data_vencimento DATE NOT NULL,
                parcela_atual INTEGER,
                total_parcelas INTEGER,
                status TEXT DEFAULT 'Aberto'
            )
        ''')
    print("[Banco] Tabela 'boletos' verificada/criada com sucesso.")

def calcular_novo_mes(data_base: datetime, meses_a_adicionar: int) -> str:
    """
    Avança ou recua exatamente N meses mantendo o dia fixo do vencimento, 
    respeitando meses de 28, 30 e 31 dias (inclusive anos bissextos).
    """
    ano = data_base.year + (data_base.month + meses_a_adicionar - 1) // 12
    mes = (data_base.month + meses_a_adicionar - 1) % 12 + 1
    ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia_mes)
    return datetime(ano, mes, dia).strftime('%Y-%m-%d')

def cadastrar_boleto(distribuidora, numero_nota, valor, data_emissao, data_vencimento, parcela_atual, total_parcelas):
    vencimento_base = datetime.strptime(data_vencimento, '%Y-%m-%d')
    nota_limpa = (numero_nota or 'S/N').strip()
    dist_limpa = distribuidora.strip()
    emissao_limpa = data_emissao.strip() if data_emissao else datetime.now().strftime('%Y-%m-%d')

    if parcela_atual > total_parcelas:
        raise ValueError("A parcela atual não pode ser maior que o total de parcelas.")

    with obter_conexao() as conexao:
        cursor = conexao.cursor()

        # 1. Se a compra começa de uma parcela avançada (ex: parcela 2 de 4),
        # registra as parcelas passadas como 'Pago' para manter o histórico 100% consistente
        for i in range(1, parcela_atual):
            salto_meses = i - parcela_atual
            venc_anterior = calcular_novo_mes(vencimento_base, salto_meses)
            cursor.execute('''
                INSERT INTO boletos (
                    distribuidora, numero_nota, valor_parcela, data_emissao, 
                    data_vencimento, parcela_atual, total_parcelas, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pago')
            ''', (dist_limpa, nota_limpa, float(valor), emissao_limpa, venc_anterior, i, total_parcelas))

        # 2. Registra as parcelas ativas a partir da parcela inicial como 'Aberto'
        for i in range(parcela_atual, total_parcelas + 1):
            salto_meses = i - parcela_atual
            novo_vencimento = calcular_novo_mes(vencimento_base, salto_meses)
            cursor.execute('''
                INSERT INTO boletos (
                    distribuidora, numero_nota, valor_parcela, data_emissao, 
                    data_vencimento, parcela_atual, total_parcelas, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Aberto')
            ''', (dist_limpa, nota_limpa, float(valor), emissao_limpa, novo_vencimento, i, total_parcelas))
            
    print(f"[Banco] Compra {nota_limpa} ({dist_limpa}) cadastrada com {total_parcelas} parcelas totais.")

def listar_boletos():
    with obter_conexao() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, distribuidora, numero_nota, valor_parcela, data_emissao, data_vencimento, parcela_atual, total_parcelas, status FROM boletos ORDER BY data_vencimento ASC")
        return [dict(linha) for linha in cursor.fetchall()]