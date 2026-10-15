# ⚡ AutoVision PRO - Gestão Financeira & Controle de Boletos

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)

> Sistema desktop completo para gestão financeira de autopeças e oficinas mecânicas, com projeção automática de parcelas, gráficos analíticos interativos e exportação contábil para Excel.

---

## 🎯 Problema Resolvido
Em oficinas mecânicas e comércios locais, compras de peças com distribuidoras costumam ser faturadas em múltiplas parcelas com notas fiscais distintas. A ausência de um sistema dedicado causa:
- Atrasos de pagamento e juros desnecessários.
- Dificuldade em prever o fluxo de caixa dos meses seguintes.
- Falta de controle visual de quais parcelas de uma mesma compra já foram quitadas.

O **AutoVision** centraliza essas compras, agrupa as parcelas por nota fiscal/fornecedor e gera métricas instantâneas de pendências e quitações.

---

## 🚀 Principais Funcionalidades

- **Dashboard Financeiro em Tempo Real:** KPIs de montante pendente, total quitado e volume de boletos em aberto.
- **Gráficos Dinâmicos (Chart.js):** Visão em Rosca (*Donut*), Distribuição por Fornecedor (Barras) e Linha do Tempo de Despesas futuras.
- **Projeção Inteligente de Parcelas:** Calendário automático respeitando meses de 28, 30 e 31 dias (inclusive anos bissextos). Suporta cadastro retroativo com marcação automática de parcelas passadas como quitadas.
- **Segurança de Ações (Toast com Undo):** Lixeira de compra completa com janela de 15 segundos para desfazer a exclusão acidental.
- **Estorno Rápido:** Possibilidade de reabrir parcelas quitadas por engano sem corromper o histórico.
- **Exportação Profissional em Excel (.xlsx):** Relatório estilizado via OpenPyXL com formatação monetária, fórmulas nativas (`SUBTOTAL`, `SUMIF`) e cabeçalhos corporativos.
- **Backup Online Transacional:** Rotina de segurança diária utilizando a API de backup nativo a quente do SQLite.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python** com **FastAPI** (Arquitetura REST assíncrona com ciclo de vida via gerenciador de contexto `lifespan`).
- **Pydantic v2** para validação estrita de esquemas e tipos.
- **SQLite 3** operando em modo **WAL (Write-Ahead Logging)** com conexão atômica e prevenção de concorrência.
- **OpenPyXL** para renderização de planilhas formatadas.

### Frontend
- **Vue 3** (Composition API com `<script setup>`).
- **Vite** para compilação rápida de assets.
- **Chart.js** & **vue-chartjs** para renderização gráfica reativa.
- **CSS3 Dark Cockpit** responsivo, sem dependência de bibliotecas de componentes pesadas.

### Distribuição Desktop
- **PyInstaller** configurado para gerar executável portátil `.exe` para Windows com ícone customizado e recursos embutidos.

---

## 💻 Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior
- Node.js 18 ou superior

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/autovision.git
cd autovision