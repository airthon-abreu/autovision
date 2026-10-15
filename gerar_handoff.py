import os

# Define o nome do arquivo de saída consolidado
ARQUIVO_SAIDA = "Codigo_Completo.txt"

# Pastas e arquivos que queremos ler e juntar
DIRETORIOS_ALVO = ["backend", "frontend/src"]
EXTENSOES_PERMITIDAS = [".py", ".vue", ".js", ".html", ".css", ".json"]

# Pastas ou arquivos que devem ser ignorados para não poluir o handoff
ITENS_IGNORADOS = ["node_modules", "venv", "__pycache__", ".git", "dist", "build"]

def gerar_handoff():
    print(f"Iniciando consolidação do projeto para: {ARQUIVO_SAIDA}...\n")
    
    total_arquivos = 0

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f_saida:
        f_saida.write("# HAHNGOFF DE CÓDIGO - SISTEMA DE CONTROLE DE BOLETOS\n")
        f_saida.write("# Este arquivo consolida o código-fonte atual para análise e suporte.\n\n")

        for caminho_base in DIRETORIOS_ALVO:
            if not os.path.exists(caminho_base):
                print(f"[Aviso] O diretório '{caminho_base}' não foi encontrado. Pulando...")
                continue

            for raiz, dirs, arquivos in os.walk(caminho_base):
                # Remove pastas indesejadas da varredura
                dirs[:] = [d for d in dirs if d not in ITENS_IGNORADOS]

                for arquivo in arquivos:
                    extensao = os.path.splitext(arquivo)[1]
                    if extensao in EXTENSOES_PERMITIDAS:
                        caminho_completo = os.path.join(raiz, arquivo)
                        
                        print(f"Lendo e incluindo: {caminho_completo}")
                        
                        f_saida.write(f"\n{'='*60}\n")
                        f_saida.write(f"CAMINHO DO FICHEIRO: {caminho_completo}\n")
                        f_saida.write(f"{'='*60}\n\n")

                        try:
                            with open(caminho_completo, "r", encoding="utf-8") as f_entrada:
                                f_saida.write(f_entrada.read())
                            f_saida.write("\n\n")
                            total_arquivos += 1
                        except Exception as e:
                            f_saida.write(f"Erro ao ler o ficheiro: {e}\n\n")

    print(f"\n[Sucesso] Handoff gerado! Total de {total_arquivos} arquivos consolidados em '{ARQUIVO_SAIDA}'.")

if __name__ == "__main__":
    gerar_handoff()