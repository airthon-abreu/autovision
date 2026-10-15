<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import GraficoMensal from './components/GraficoMensal.vue'

const abaAtual = ref('dashboard')
const modoVisualizacao = ref('compras')
const comprasExpandidas = ref({})
const formularioAberto = ref(false)

const boletosDashboard = ref([])
const boletosGestao = ref([])
const erroDeConexao = ref(null)

const toastUndo = ref({
  visivel: false,
  mensagem: '',
  dadosBackup: null,
  tempoRestante: 15,
  intervaloId: null
})

const filtroDistribuidora = ref('')
const filtroDiasVencimento = ref(null)
const filtroStatus = ref('Aberto')

let debounceBuscaTimeout = null

const obterDataHojeIso = () => new Date().toISOString().split('T')[0]

const novoBoleto = ref({
  distribuidora: '',
  numero_nota: '',
  valor_parcela: null,
  data_emissao: obterDataHojeIso(),
  data_vencimento: '',
  parcela_atual: 1,
  total_parcelas: 1
})

const obterApiUrl = (endpoint) => {
  const isDev = import.meta.env.DEV
  const base = isDev ? 'http://127.0.0.1:9000' : ''
  return `${base}${endpoint}`
}

const formatarDataBR = (dataIso) => {
  if (!dataIso) return ''
  const partes = dataIso.split('-')
  if (partes.length !== 3) return dataIso
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

const formatarMoeda = (val) => {
  return Number(val || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const alternarExpansao = (chave) => {
  comprasExpandidas.value[chave] = !comprasExpandidas.value[chave]
}

const carregarDashboard = async () => {
  try {
    const res = await fetch(obterApiUrl('/boletos?status=Todos'))
    if (!res.ok) throw new Error('Falha ao carregar dashboard.')
    boletosDashboard.value = await res.json()
  } catch (erro) {
    erroDeConexao.value = erro.message
  }
}

const carregarGestao = async () => {
  try {
    let url = `/boletos?status=${filtroStatus.value}&`
    if (filtroDistribuidora.value.trim()) url += `distribuidora=${encodeURIComponent(filtroDistribuidora.value.trim())}&`
    if (filtroDiasVencimento.value !== null && filtroDiasVencimento.value !== '') url += `dias_vencimento=${filtroDiasVencimento.value}&`

    const res = await fetch(obterApiUrl(url))
    if (!res.ok) throw new Error('Falha ao buscar dados.')
    boletosGestao.value = await res.json()
  } catch (erro) {
    erroDeConexao.value = erro.message
  }
}

const aplicarFiltroComDebounce = () => {
  clearTimeout(debounceBuscaTimeout)
  debounceBuscaTimeout = setTimeout(() => {
    carregarGestao()
  }, 250)
}

const recarregarTudo = async () => {
  erroDeConexao.value = null
  await Promise.all([carregarDashboard(), carregarGestao()])
}

const salvarBoleto = async () => {
  if (!novoBoleto.value.distribuidora.trim()) {
    alert('Erro: Informe a distribuidora.')
    return
  }

  if (!novoBoleto.value.data_vencimento) {
    alert('Erro: Informe a data do primeiro vencimento.')
    return
  }

  if (!novoBoleto.value.valor_parcela || Number(novoBoleto.value.valor_parcela) <= 0) {
    alert('Erro: O valor da parcela deve ser maior que zero.')
    return
  }

  if (novoBoleto.value.parcela_atual > novoBoleto.value.total_parcelas) {
    alert('Erro: A parcela inicial não pode ser superior ao total de parcelas.')
    return
  }

  try {
    const res = await fetch(obterApiUrl('/boletos'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(novoBoleto.value)
    })
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'Falha ao salvar compra.')
    }
    
    await recarregarTudo()
    alert('Compra cadastrada e parcelas projetadas com sucesso!')
    
    novoBoleto.value.distribuidora = ''
    novoBoleto.value.numero_nota = ''
    novoBoleto.value.valor_parcela = null
    novoBoleto.value.data_vencimento = ''
    novoBoleto.value.data_emissao = obterDataHojeIso()
    novoBoleto.value.parcela_atual = 1
    novoBoleto.value.total_parcelas = 1
    formularioAberto.value = false
    abaAtual.value = 'gestao'
  } catch (erro) {
    alert("Erro ao salvar: " + erro.message)
  }
}

const marcarComoPago = async (id) => {
  if (!confirm("Confirmar a quitação desta parcela?")) return
  try {
    const res = await fetch(obterApiUrl(`/boletos/${id}/pagar`), { method: 'PUT' })
    if (!res.ok) throw new Error('Falha ao atualizar status.')
    await recarregarTudo()
  } catch (erro) {
    alert("Erro ao quitar: " + erro.message)
  }
}

const reabrirBoleto = async (id) => {
  if (!confirm("Deseja reabrir esta parcela e torná-la pendente novamente?")) return
  try {
    const res = await fetch(obterApiUrl(`/boletos/${id}/reabrir`), { method: 'PUT' })
    if (!res.ok) throw new Error('Falha ao reabrir parcela.')
    await recarregarTudo()
  } catch (erro) {
    alert("Erro ao reabrir: " + erro.message)
  }
}

const apagarCompra = async (compra) => {
  const confirmou = confirm(
    `Tem certeza que deseja apagar a compra "${compra.distribuidora}" (NF: ${compra.numero_nota}) com todas as ${compra.total_parcelas} parcelas registradas?`
  )
  if (!confirmou) return

  try {
    const idsParaExcluir = compra.todos_ids
    const parcelasBackup = compra.todas_parcelas_info

    const res = await fetch(obterApiUrl('/compras/excluir'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: idsParaExcluir })
    })

    if (!res.ok) throw new Error('Falha ao excluir compra.')

    await recarregarTudo()

    if (toastUndo.value.intervaloId) clearInterval(toastUndo.value.intervaloId)

    toastUndo.value.visivel = true
    toastUndo.value.mensagem = `Compra "${compra.distribuidora}" (NF: ${compra.numero_nota}) excluída.`
    toastUndo.value.dadosBackup = parcelasBackup
    toastUndo.value.tempoRestante = 15

    toastUndo.value.intervaloId = setInterval(() => {
      toastUndo.value.tempoRestante--
      if (toastUndo.value.tempoRestante <= 0) {
        fecharToast()
      }
    }, 1000)

  } catch (erro) {
    alert("Erro ao excluir: " + erro.message)
  }
}

const desfazerExclusao = async () => {
  if (!toastUndo.value.dadosBackup) return

  try {
    const res = await fetch(obterApiUrl('/compras/restaurar'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parcelas: toastUndo.value.dadosBackup })
    })

    if (!res.ok) throw new Error('Falha ao restaurar compra.')

    fecharToast()
    await recarregarTudo()
  } catch (erro) {
    alert("Erro ao desfazer exclusão: " + erro.message)
  }
}

const fecharToast = () => {
  if (toastUndo.value.intervaloId) clearInterval(toastUndo.value.intervaloId)
  toastUndo.value.visivel = false
  toastUndo.value.dadosBackup = null
}

const exportarExcel = () => {
  let url = `/boletos/exportar/excel?status=${filtroStatus.value}&`
  if (filtroDistribuidora.value.trim()) url += `distribuidora=${encodeURIComponent(filtroDistribuidora.value.trim())}&`
  if (filtroDiasVencimento.value !== null && filtroDiasVencimento.value !== '') url += `dias_vencimento=${filtroDiasVencimento.value}&`
  window.open(obterApiUrl(url), '_blank')
}

const comprasAgrupadas = computed(() => {
  const grupos = {}

  boletosGestao.value.forEach(b => {
    const chave = b.compra_chave
    const resumo = b.compra_resumo

    if (!grupos[chave]) {
      grupos[chave] = {
        chave,
        distribuidora: b.distribuidora,
        numero_nota: b.numero_nota,
        data_inicio: resumo.data_inicio,
        data_termino: resumo.data_termino,
        total_parcelas: resumo.total_parcelas,
        qtd_pagas: resumo.qtd_pagas,
        valor_total: resumo.valor_total,
        total_pago: resumo.total_pago,
        total_pendente: resumo.total_pendente,
        todos_ids: resumo.todos_ids_compra,
        todas_parcelas_info: resumo.todas_parcelas_info,
        parcelas: []
      }
    }
    grupos[chave].parcelas.push(b)
  })

  Object.values(grupos).forEach(grupo => {
    grupo.parcelas.sort((a, b) => a.parcela_atual - b.parcela_atual)
  })

  return Object.values(grupos).sort((a, b) => (a.data_inicio || '').localeCompare(b.data_inicio || ''))
})

const totalPendenteGeral = computed(() => {
  return boletosDashboard.value.reduce((acc, b) => b.status !== 'Pago' ? acc + b.valor_parcela : acc, 0)
})

const totalPagoGeral = computed(() => {
  return boletosDashboard.value.reduce((acc, b) => b.status === 'Pago' ? acc + b.valor_parcela : acc, 0)
})

const parcelasPendentesQtd = computed(() => {
  return boletosDashboard.value.filter(b => b.status !== 'Pago').length
})

const limparFiltros = () => {
  filtroDistribuidora.value = ''
  filtroDiasVencimento.value = null
  filtroStatus.value = 'Aberto'
  carregarGestao()
}

onMounted(() => recarregarTudo())

onUnmounted(() => {
  if (toastUndo.value.intervaloId) clearInterval(toastUndo.value.intervaloId)
  clearTimeout(debounceBuscaTimeout)
})
</script>

<template>
  <div class="layout-app">
    <!-- HEADER -->
    <header class="header-principal">
      <div class="marca-app">
        <img src="/logo.png" alt="AutoVision Logo" class="icone-logo" />
        <div>
          <div class="linha-marca">
            <h1 class="titulo-app">Auto<span class="destaque-vision">Vision</span></h1>
            <span class="badge-versao">v1.0 PRO</span>
          </div>
          <span class="subtitulo-app">Gestão Inteligente de Boletos & Fornecedores</span>
        </div>
      </div>

      <nav class="nav-segmentada">
        <button 
          @click="abaAtual = 'dashboard'" 
          :class="['btn-aba', { 'btn-aba-ativa': abaAtual === 'dashboard' }]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          Dashboard
        </button>
        <button 
          @click="abaAtual = 'gestao'" 
          :class="['btn-aba', { 'btn-aba-ativa': abaAtual === 'gestao' }]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
          </svg>
          Gestão & Compras
        </button>
      </nav>
    </header>

    <main class="conteudo-principal">

      <!-- ABA 1: DASHBOARD -->
      <section v-if="abaAtual === 'dashboard'">
        <div class="banner-hero">
          <div class="info-hero">
            <h2 class="titulo-hero">Visão Geral da Oficina</h2>
            <p class="desc-hero">Monitore contas pendentes, controle prazos de distribuidoras e evite juros.</p>
          </div>
          <button @click="exportarExcel" class="btn-excel-topo">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Baixar Relatório (.XLSX)
          </button>
        </div>

        <div class="grid-kpis">
          <div class="card-kpi glow-ciano">
            <div class="kpi-icone icone-ciano">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div>
              <span class="kpi-rotulo">Total a Pagar (Pendente)</span>
              <div class="kpi-valor valor-ciano">{{ formatarMoeda(totalPendenteGeral) }}</div>
            </div>
          </div>

          <div class="card-kpi glow-esmeralda">
            <div class="kpi-icone icone-esmeralda">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <div>
              <span class="kpi-rotulo">Total Já Quitado</span>
              <div class="kpi-valor valor-esmeralda">{{ formatarMoeda(totalPagoGeral) }}</div>
            </div>
          </div>

          <div class="card-kpi glow-indigo">
            <div class="kpi-icone icone-indigo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              </svg>
            </div>
            <div>
              <span class="kpi-rotulo">Boletos em Aberto</span>
              <div class="kpi-valor valor-indigo">{{ parcelasPendentesQtd }} <span style="font-size: 15px; font-weight: normal; color: #94a3b8;">parcelas</span></div>
            </div>
          </div>
        </div>

        <GraficoMensal :boletos="boletosDashboard" />
      </section>

      <!-- ABA 2: GESTÃO E COMPRAS -->
      <section v-if="abaAtual === 'gestao'">
        <div class="barra-topo-gestao">
          <div>
            <h3 style="font-size: 18px; font-weight: 700; color: #f8fafc; margin: 0;">Gestão Financeira de Compras</h3>
            <p style="font-size: 13px; color: #94a3b8; margin: 2px 0 0 0;">Controle agrupado por fornecedor com projeção de vencimentos</p>
          </div>
          
          <button 
            @click="formularioAberto = !formularioAberto" 
            :class="['btn-toggle-novo', { 'btn-toggle-ativo': formularioAberto }]"
          >
            <span v-if="!formularioAberto">➕ Nova Compra</span>
            <span v-else>✖ Fechar Formulário</span>
          </button>
        </div>

        <!-- FORMULÁRIO -->
        <div v-if="formularioAberto" class="card-cockpit painel-animado">
          <div class="card-topo-titulo">
            <div class="circulo-icone icone-ciano">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </div>
            <div>
              <h3 style="font-size: 16px; font-weight: 700; color: #f8fafc;">Cadastrar Nova Compra</h3>
              <p style="font-size: 12px; color: #94a3b8;">Insira os dados da nota para projetar as parcelas mensais</p>
            </div>
          </div>

          <form @submit.prevent="salvarBoleto" class="grid-formulario">
            <div class="campo-grupo">
              <label class="rotulo">Distribuidora:</label>
              <input v-model="novoBoleto.distribuidora" required type="text" placeholder="Ex: Bosch, Nakata, Tecfil" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">Nº da Nota:</label>
              <input v-model="novoBoleto.numero_nota" type="text" placeholder="Ex: NF-1234" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">Valor da Parcela (R$):</label>
              <input v-model.number="novoBoleto.valor_parcela" required type="number" step="0.01" min="0.01" placeholder="0,00" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">Data de Emissão:</label>
              <input v-model="novoBoleto.data_emissao" required type="date" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">1º Vencimento:</label>
              <input v-model="novoBoleto.data_vencimento" required type="date" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">Parcela Inicial:</label>
              <input v-model.number="novoBoleto.parcela_atual" required type="number" min="1" class="input-cockpit">
            </div>

            <div class="campo-grupo">
              <label class="rotulo">Total de Parcelas:</label>
              <input v-model.number="novoBoleto.total_parcelas" required type="number" :min="novoBoleto.parcela_atual || 1" class="input-cockpit">
            </div>

            <div class="area-submit">
              <button type="submit" class="btn-gradiente-acao">
                Salvar Compra e Projetar Parcelas
              </button>
            </div>
          </form>
        </div>

        <!-- FILTROS -->
        <div class="card-cockpit" style="padding: 16px 20px; margin-bottom: 20px;">
          <div class="header-filtros">
            <h4 style="font-size: 14px; font-weight: 700; color: #f1f5f9;">Filtros de Consulta</h4>
            
            <div class="seletor-modo-lista">
              <button 
                @click="modoVisualizacao = 'compras'" 
                :class="['btn-modo', { 'btn-modo-ativo': modoVisualizacao === 'compras' }]"
              >
                🗂️ Agrupado por Compra
              </button>
              <button 
                @click="modoVisualizacao = 'parcelas'" 
                :class="['btn-modo', { 'btn-modo-ativo': modoVisualizacao === 'parcelas' }]"
              >
                📅 Visão Cronológica
              </button>
            </div>
          </div>

          <div class="grid-filtros-campos">
            <div style="flex: 1; min-width: 200px;">
              <label class="rotulo">Distribuidora:</label>
              <input 
                v-model="filtroDistribuidora" 
                @input="aplicarFiltroComDebounce" 
                type="text" 
                placeholder="Buscar por fornecedor..." 
                class="input-cockpit"
              >
            </div>
            <div style="width: 140px;">
              <label class="rotulo">Vencimento em:</label>
              <input 
                v-model.number="filtroDiasVencimento" 
                @input="aplicarFiltroComDebounce" 
                type="number" 
                min="0" 
                placeholder="Ex: 30 dias" 
                class="input-cockpit"
              >
            </div>
            <div style="width: 160px;">
              <label class="rotulo">Status:</label>
              <select v-model="filtroStatus" @change="carregarGestao" class="input-cockpit">
                <option value="Aberto">Em Aberto</option>
                <option value="Pago">Quitados</option>
                <option value="Todos">Todos os Status</option>
              </select>
            </div>
            <button @click="limparFiltros" class="btn-limpar-cockpit">Limpar</button>
          </div>
        </div>

        <div v-if="erroDeConexao" class="alerta-erro">
          Erro de conexão: {{ erroDeConexao }}
        </div>
        
        <div v-else-if="boletosGestao.length === 0" class="alerta-vazio">
          Nenhum registro encontrado para este filtro.
        </div>

        <!-- MODO 1: CARDS AGRUPADOS -->
        <div v-else-if="modoVisualizacao === 'compras'" class="grid-compras-organizado">
          <div 
            v-for="compra in comprasAgrupadas" 
            :key="compra.chave" 
            class="card-compra-moderno"
          >
            <div class="compra-topo">
              <div>
                <div class="linha-titulo-nota">
                  <h3 class="nome-distribuidora">{{ compra.distribuidora }}</h3>
                  <span class="badge-nota">NF: {{ compra.numero_nota }}</span>
                </div>
                <div class="periodo-compra">
                  <span>📅 {{ formatarDataBR(compra.data_inicio) }}</span>
                  <span class="seta-separador">➔</span>
                  <span>🏁 {{ formatarDataBR(compra.data_termino) }}</span>
                  <span class="separador-ponto">•</span>
                  <span>{{ compra.total_parcelas }} parcela(s)</span>
                </div>
              </div>

              <div class="topo-acoes-compra">
                <span 
                  :class="['badge-progresso', compra.qtd_pagas === compra.total_parcelas ? 'badge-concluido' : 'badge-pendente']"
                >
                  {{ compra.qtd_pagas }} de {{ compra.total_parcelas }} quitadas
                </span>

                <button 
                  @click="apagarCompra(compra)" 
                  class="btn-apagar-compra" 
                  title="Apagar esta compra inteira"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                  </svg>
                </button>
              </div>
            </div>

            <div class="trilho-progresso-card">
              <div 
                class="barra-progresso-card" 
                :style="{ width: ((compra.qtd_pagas / compra.total_parcelas) * 100) + '%' }"
              ></div>
            </div>

            <div class="grid-resumo-3colunas">
              <div class="bloco-valor">
                <span class="rotulo-mini">Valor Total</span>
                <strong class="valor-destaque-total">{{ formatarMoeda(compra.valor_total) }}</strong>
              </div>
              <div class="bloco-valor">
                <span class="rotulo-mini">Já Quitado</span>
                <strong class="valor-destaque-pago">{{ formatarMoeda(compra.total_pago) }}</strong>
              </div>
              <div class="bloco-valor">
                <span class="rotulo-mini">Pendente</span>
                <strong class="valor-destaque-pendente">{{ formatarMoeda(compra.total_pendente) }}</strong>
              </div>
            </div>

            <div class="rodape-card-compra">
              <button @click="alternarExpansao(compra.chave)" class="btn-toggle-parcelas">
                <span>{{ comprasExpandidas[compra.chave] ? 'Ocultar Parcelas' : 'Visualizar Parcelas' }} ({{ compra.parcelas.length }})</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: comprasExpandidas[compra.chave] ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>

            <div v-if="comprasExpandidas[compra.chave]" class="container-subparcelas">
              <div 
                v-for="p in compra.parcelas" 
                :key="p.id" 
                :class="['subcard-parcela', p.status === 'Pago' ? 'parcela-paga' : 'parcela-aberta']"
              >
                <div>
                  <span style="font-weight: 700; color: #f8fafc;">Parcela {{ p.parcela_atual }}/{{ p.total_parcelas }}</span>
                  <span class="separador-ponto">•</span>
                  <span>Venc: <strong style="color: #00d2ff;">{{ formatarDataBR(p.data_vencimento) }}</strong></span>
                </div>

                <div class="acoes-parcela">
                  <span class="valor-parcela-item">{{ formatarMoeda(p.valor_parcela) }}</span>
                  <span :class="['pill-status', p.status === 'Pago' ? 'pill-pago' : 'pill-aberto']">
                    {{ p.status === 'Pago' ? 'PAGO' : 'ABERTO' }}
                  </span>
                  <button 
                    v-if="p.status === 'Aberto'" 
                    @click="marcarComoPago(p.id)" 
                    class="btn-quitar-neon"
                  >
                    ✓ Quitar
                  </button>
                  <button 
                    v-else-if="p.status === 'Pago'" 
                    @click="reabrirBoleto(p.id)" 
                    class="btn-reabrir-discreto"
                    title="Desfazer quitação desta parcela"
                  >
                    ↩ Reabrir
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- MODO 2: VISÃO CRONOLÓGICA -->
        <div v-else class="grid-compras-organizado">
          <div 
            v-for="b in boletosGestao" 
            :key="b.id" 
            :class="['card-cronologico', b.status === 'Pago' ? 'parcela-paga' : 'parcela-aberta']"
          >
            <div class="linha-topo-cronologico">
              <div>
                <strong style="font-size: 16px; color: #f8fafc;">{{ b.distribuidora }}</strong>
                <span class="badge-nota" style="margin-left: 8px;">NF: {{ b.numero_nota }}</span>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <span class="badge-progresso badge-pendente">Parcela {{ b.parcela_atual }} de {{ b.total_parcelas }}</span>
                <button v-if="b.status === 'Aberto'" @click="marcarComoPago(b.id)" class="btn-quitar-neon">✓ Quitar</button>
                <button v-else-if="b.status === 'Pago'" @click="reabrirBoleto(b.id)" class="btn-reabrir-discreto" title="Desfazer quitação">↩ Reabrir</button>
              </div>
            </div>

            <div style="font-size: 13px; color: #94a3b8; margin: 10px 0;">
              Vencimento: <strong style="color: #00d2ff;">{{ formatarDataBR(b.data_vencimento) }}</strong> 
              <span class="separador-ponto">•</span>
              Período: {{ formatarDataBR(b.compra_resumo.data_inicio) }} ➔ {{ formatarDataBR(b.compra_resumo.data_termino) }}
            </div>

            <div class="rodape-cronologico">
              <span>Parcela: <strong style="color: #00d2ff;">{{ formatarMoeda(b.valor_parcela) }}</strong></span>
              <span>Total da Compra: <strong style="color: #f1f5f9;">{{ formatarMoeda(b.compra_resumo.valor_total) }}</strong></span>
            </div>
          </div>
        </div>
      </section>

    </main>

    <!-- TOAST DE DESFAZER EXCLUSÃO -->
    <transition name="toast-anim">
      <div v-if="toastUndo.visivel" class="toast-undo-container">
        <div class="toast-undo-conteudo">
          <div class="toast-info">
            <span class="icone-alerta-toast">🗑️</span>
            <span>{{ toastUndo.mensagem }}</span>
          </div>

          <div class="toast-botoes">
            <button @click="desfazerExclusao" class="btn-desfazer-toast">
              ↩️ Desfazer ({{ toastUndo.tempoRestante }}s)
            </button>
            <button @click="fecharToast" class="btn-fechar-toast" title="Dispensar">
              ✖
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.layout-app {
  max-width: 1140px;
  margin: 0 auto;
  padding: 24px 20px;
  position: relative;
}

.header-principal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.marca-app {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icone-logo {
  width: 70px;
  height: 70px;
  border-radius: 16px;
  box-shadow: 0 0 20px rgba(0, 210, 255, 0.4);
  transition: transform 0.2s ease;
}

.icone-logo:hover {
  transform: scale(1.03);
}

.linha-marca {
  display: flex;
  align-items: center;
  gap: 8px;
}

.titulo-app {
  font-size: 26px;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.5px;
}

.destaque-vision {
  background: linear-gradient(135deg, #00d2ff, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.badge-versao {
  background: #1e293b;
  color: #00d2ff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 6px;
  border: 1px solid #334155;
}

.subtitulo-app {
  font-size: 13px;
  color: #94a3b8;
}

.nav-segmentada {
  display: flex;
  background: #0f172a;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid #1e293b;
  gap: 4px;
}

.btn-aba {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-aba-ativa {
  background: #1e293b;
  color: #00d2ff;
  box-shadow: 0 0 10px rgba(0, 210, 255, 0.15);
}

.banner-hero {
  background: linear-gradient(135deg, #0f172a 0%, #111d38 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 22px 26px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.titulo-hero {
  font-size: 20px;
  font-weight: 800;
  color: #f8fafc;
}

.desc-hero {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

.btn-excel-topo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #059669, #10b981);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
  transition: transform 0.2s;
}

.btn-excel-topo:hover {
  transform: translateY(-1px);
}

.grid-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.card-kpi {
  background: #0f172a;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid #1e293b;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.glow-ciano { border-color: rgba(0, 210, 255, 0.3); }
.glow-esmeralda { border-color: rgba(16, 185, 129, 0.3); }
.glow-indigo { border-color: rgba(99, 102, 241, 0.3); }

.kpi-icone {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icone-ciano { background: rgba(0, 210, 255, 0.1); color: #00d2ff; }
.icone-esmeralda { background: rgba(16, 185, 129, 0.1); color: #10b981; }
.icone-indigo { background: rgba(99, 102, 241, 0.1); color: #818cf8; }

.kpi-rotulo {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
  display: block;
}

.kpi-valor {
  font-size: 24px;
  font-weight: 800;
  color: #f8fafc;
  margin-top: 2px;
}

.valor-ciano { color: #00d2ff; text-shadow: 0 0 10px rgba(0, 210, 255, 0.25); }
.valor-esmeralda { color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.25); }
.valor-indigo { color: #818cf8; }

.barra-topo-gestao {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.btn-toggle-novo {
  padding: 9px 18px;
  background: linear-gradient(135deg, #0284c7, #00d2ff);
  color: #080d1a;
  border: none;
  border-radius: 8px;
  font-weight: 800;
  font-size: 13px;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.3);
  transition: all 0.2s ease;
}

.btn-toggle-novo:hover {
  transform: translateY(-1px);
}

.btn-toggle-ativo {
  background: #334155;
  color: #f8fafc;
  box-shadow: none;
}

.card-cockpit {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 22px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.painel-animado {
  animation: slideDown 0.25s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-topo-titulo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.circulo-icone {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.grid-formulario {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.campo-grupo {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.rotulo {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

.input-cockpit {
  padding: 9px 12px;
  background: #131c31;
  border: 1px solid #334155;
  border-radius: 8px;
  font-size: 14px;
  color: #f8fafc;
  outline: none;
  transition: all 0.2s ease;
}

.input-cockpit:focus {
  border-color: #00d2ff;
  box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.area-submit {
  grid-column: 1 / -1;
  margin-top: 6px;
}

.btn-gradiente-acao {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #0284c7, #00d2ff);
  color: #080d1a;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.3);
}

.header-filtros {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.seletor-modo-lista {
  display: flex;
  background: #131c31;
  padding: 3px;
  border-radius: 8px;
  border: 1px solid #334155;
}

.btn-modo {
  padding: 5px 12px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
}

.btn-modo-ativo {
  background: #1e293b;
  color: #00d2ff;
}

.grid-filtros-campos {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.btn-limpar-cockpit {
  padding: 9px 15px;
  background: #1e293b;
  color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.grid-compras-organizado {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 16px;
}

@media (max-width: 600px) {
  .grid-compras-organizado {
    grid-template-columns: 1fr;
  }
}

.card-compra-moderno {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  transition: border-color 0.2s ease;
}

.card-compra-moderno:hover {
  border-color: rgba(0, 210, 255, 0.4);
}

.compra-topo {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.linha-titulo-nota {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nome-distribuidora {
  font-size: 17px;
  font-weight: 800;
  color: #f8fafc;
}

.badge-nota {
  background: #1e293b;
  color: #00d2ff;
  border: 1px solid #334155;
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.periodo-compra {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.seta-separador { color: #00d2ff; font-size: 11px; }
.separador-ponto { color: #475569; }

.topo-acoes-compra {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge-progresso {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.badge-pendente {
  background: rgba(0, 210, 255, 0.1);
  color: #00d2ff;
  border: 1px solid rgba(0, 210, 255, 0.25);
}

.badge-concluido {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.btn-apagar-compra {
  background: #1e293b;
  border: 1px solid #334155;
  color: #94a3b8;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-apagar-compra:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-color: #ef4444;
  transform: scale(1.05);
}

.trilho-progresso-card {
  height: 5px;
  background: #1e293b;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 14px;
}

.barra-progresso-card {
  height: 100%;
  background: linear-gradient(90deg, #00d2ff, #10b981);
  border-radius: 999px;
  transition: width 0.4s ease;
}

.grid-resumo-3colunas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  background: #131c31;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #1e293b;
  margin-bottom: 12px;
}

.bloco-valor {
  text-align: center;
}

.rotulo-mini {
  display: block;
  font-size: 10px;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
  margin-bottom: 2px;
}

.valor-destaque-total { font-size: 15px; color: #f8fafc; }
.valor-destaque-pago { font-size: 15px; color: #10b981; }
.valor-destaque-pendente { font-size: 15px; color: #ef4444; }

.btn-toggle-parcelas {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: #131c31;
  border: 1px solid #334155;
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #00d2ff;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-toggle-parcelas:hover {
  background: #1a2540;
}

.container-subparcelas {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #334155;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subcard-parcela {
  padding: 8px 12px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  background: #131c31;
}

.parcela-aberta { border: 1px solid #1e293b; border-left: 3px solid #00d2ff; }
.parcela-paga { border: 1px solid #1e293b; border-left: 3px solid #10b981; }

.acoes-parcela {
  display: flex;
  align-items: center;
  gap: 8px;
}

.valor-parcela-item {
  font-weight: 700;
  color: #f8fafc;
}

.pill-status {
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}

.pill-aberto { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.pill-pago { background: rgba(16, 185, 129, 0.15); color: #34d399; }

.btn-quitar-neon {
  padding: 4px 10px;
  background: #10b981;
  color: #080d1a;
  border: none;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-quitar-neon:hover {
  opacity: 0.9;
}

.btn-reabrir-discreto {
  padding: 3px 8px;
  background: #1e293b;
  color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reabrir-discreto:hover {
  color: #f87171;
  border-color: #ef4444;
}

.card-cronologico {
  background: #0f172a;
  padding: 14px 18px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.linha-topo-cronologico {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rodape-cronologico {
  display: flex;
  justify-content: space-between;
  background: #131c31;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 8px;
}

.alerta-erro {
  padding: 14px;
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  font-size: 14px;
}

.alerta-vazio {
  text-align: center;
  padding: 40px;
  background: #0f172a;
  border-radius: 12px;
  border: 1px dashed #334155;
  color: #94a3b8;
}

.toast-undo-container {
  position: fixed;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
}

.toast-undo-conteudo {
  background: #1e293b;
  border: 1px solid #38bdf8;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 210, 255, 0.25);
  padding: 12px 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 20px;
  color: #f8fafc;
  font-size: 14px;
}

.toast-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icone-alerta-toast {
  font-size: 18px;
}

.toast-botoes {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-desfazer-toast {
  background: linear-gradient(135deg, #0284c7, #00d2ff);
  color: #080d1a;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-weight: 800;
  font-size: 13px;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-desfazer-toast:hover {
  transform: scale(1.05);
}

.btn-fechar-toast {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
}

.btn-fechar-toast:hover {
  color: #f8fafc;
}

.toast-anim-enter-active, .toast-anim-leave-active {
  transition: all 0.3s ease;
}
.toast-anim-enter-from, .toast-anim-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}
</style>