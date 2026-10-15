<script setup>
import { ref, computed, watch } from 'vue'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import { 
  Chart as ChartJS, Title, Tooltip, Legend, ArcElement, 
  BarElement, CategoryScale, LinearScale, PointElement, LineElement, Filler 
} from 'chart.js'

ChartJS.register(
  Title, Tooltip, Legend, ArcElement, 
  BarElement, CategoryScale, LinearScale, PointElement, LineElement, Filler
)

const props = defineProps({
  boletos: {
    type: Array,
    required: true
  }
})

const tipoGrafico = ref('donut')

const paletaCores = [
  '#00d2ff', '#10b981', '#6366f1', '#f59e0b', '#ec4899',
  '#06b6d4', '#14b8a6', '#8b5cf6', '#3b82f6', '#f43f5e'
]

const gerarCor = (index) => {
  if (index < paletaCores.length) return paletaCores[index]
  const hue = (index * 137.5) % 360
  return `hsl(${Math.round(hue)}, 80%, 55%)`
}

const formatarMes = (anoMes) => {
  if (!anoMes) return ''
  const partes = anoMes.split('-')
  if (partes.length < 2) return anoMes
  const mesesNomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  const mesIndex = parseInt(partes[1], 10) - 1
  return `${mesesNomes[mesIndex] || partes[1]} / ${partes[0]}`
}

const formatarMoeda = (val) => {
  return Number(val || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// Meses com contas em aberto
const mesesDisponiveis = computed(() => {
  const meses = new Set()
  props.boletos.forEach(b => {
    if (b.data_vencimento && b.status !== 'Pago') {
      meses.add(b.data_vencimento.substring(0, 7))
    }
  })
  return Array.from(meses).sort()
})

const mesSelecionado = ref('')

// Prioriza o mês atual; se não houver pendências nele, pega o primeiro com pendências
watch(mesesDisponiveis, (novosMeses) => {
  if (novosMeses.length > 0) {
    const mesAtualIso = new Date().toISOString().substring(0, 7)
    if (novosMeses.includes(mesAtualIso)) {
      mesSelecionado.value = mesAtualIso
    } else if (!mesSelecionado.value || !novosMeses.includes(mesSelecionado.value)) {
      mesSelecionado.value = novosMeses[0]
    }
  } else {
    mesSelecionado.value = ''
  }
}, { immediate: true })

const analiseFornecedoresMes = computed(() => {
  const totais = {}
  let totalGeralMes = 0

  props.boletos.forEach(b => {
    const mesAno = b.data_vencimento ? b.data_vencimento.substring(0, 7) : ''
    if (mesAno === mesSelecionado.value && b.status !== 'Pago') {
      const dist = b.distribuidora || 'Outros'
      totais[dist] = (totais[dist] || 0) + b.valor_parcela
      totalGeralMes += b.valor_parcela
    }
  })

  const lista = Object.keys(totais).map((dist, idx) => ({
    distribuidora: dist,
    valor: totais[dist],
    porcentagem: totalGeralMes > 0 ? ((totais[dist] / totalGeralMes) * 100).toFixed(1) : '0.0',
    cor: gerarCor(idx)
  })).sort((a, b) => b.valor - a.valor)

  return { lista, totalGeralMes }
})

const dadosDonut = computed(() => {
  const { lista } = analiseFornecedoresMes.value
  return {
    labels: lista.map(i => i.distribuidora),
    datasets: [{
      backgroundColor: lista.map(i => i.cor),
      data: lista.map(i => i.valor),
      borderWidth: 2,
      borderColor: '#0f172a',
      hoverOffset: 8
    }]
  }
})

const dadosBarras = computed(() => {
  const { lista } = analiseFornecedoresMes.value
  return {
    labels: lista.map(i => i.distribuidora),
    datasets: [{
      label: 'Valor a Pagar',
      backgroundColor: lista.map(i => i.cor),
      borderRadius: 6,
      data: lista.map(i => i.valor)
    }]
  }
})

const dadosLinhaDoTempo = computed(() => {
  const totaisPorMes = {}

  props.boletos.forEach(b => {
    if (b.data_vencimento && b.status !== 'Pago') {
      const mesAno = b.data_vencimento.substring(0, 7)
      totaisPorMes[mesAno] = (totaisPorMes[mesAno] || 0) + b.valor_parcela
    }
  })

  const mesesOrdenados = Object.keys(totaisPorMes).sort()
  return {
    labels: mesesOrdenados.map(formatarMes),
    datasets: [{
      label: 'Total de Contas a Pagar',
      borderColor: '#00d2ff',
      backgroundColor: 'rgba(0, 210, 255, 0.12)',
      borderWidth: 3,
      fill: true,
      tension: 0.35,
      pointBackgroundColor: '#10b981',
      pointBorderColor: '#ffffff',
      pointRadius: 5,
      pointHoverRadius: 7,
      data: mesesOrdenados.map(m => totaisPorMes[m])
    }]
  }
})

const opcoesDonut = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '74%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      borderWidth: 1,
      padding: 12,
      callbacks: { label: (c) => ` ${formatarMoeda(c.parsed)}` }
    }
  }
}

const opcoesGeraisCartesianas = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      borderWidth: 1,
      padding: 12,
      callbacks: { label: (c) => ` ${formatarMoeda(c.parsed.y !== undefined ? c.parsed.y : c.parsed)}` }
    }
  },
  scales: {
    x: {
      ticks: { color: '#94a3b8', font: { size: 11 } },
      grid: { color: '#1e293b' }
    },
    y: {
      ticks: { 
        color: '#94a3b8', 
        callback: (val) => 'R$ ' + Number(val).toLocaleString('pt-BR') 
      },
      grid: { color: '#1e293b' }
    }
  }
}
</script>

<template>
  <div class="card-grafico">
    <div class="header-grafico">
      <div>
        <h3 class="titulo-secao">Análise Financeira de Despesas</h3>
        <p class="subtitulo-secao">Escolha o modo de visualização mais conveniente</p>
      </div>

      <div class="controles-grafico">
        <div class="seletor-estilo-grafico">
          <button 
            @click="tipoGrafico = 'donut'" 
            :class="['btn-tipo-grafico', { 'btn-tipo-ativo': tipoGrafico === 'donut' }]"
          >
            🍩 Rosca
          </button>
          <button 
            @click="tipoGrafico = 'barras'" 
            :class="['btn-tipo-grafico', { 'btn-tipo-ativo': tipoGrafico === 'barras' }]"
          >
            📊 Barras
          </button>
          <button 
            @click="tipoGrafico = 'timeline'" 
            :class="['btn-tipo-grafico', { 'btn-tipo-ativo': tipoGrafico === 'timeline' }]"
          >
            📈 Linha do Tempo
          </button>
        </div>

        <div v-if="tipoGrafico !== 'timeline' && mesesDisponiveis.length > 0" class="seletor-container">
          <span class="label-seletor">Mês:</span>
          <select v-model="mesSelecionado" class="select-mes">
            <option v-for="mes in mesesDisponiveis" :key="mes" :value="mes">
              {{ formatarMes(mes) }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- MODO 1: GRÁFICO DONUT -->
    <div v-if="tipoGrafico === 'donut'">
      <div v-if="analiseFornecedoresMes.lista.length === 0" class="estado-vazio">
        <div class="icone-vazio">✨</div>
        <p style="font-weight: 600; color: #f1f5f9;">Sem contas pendentes para este mês</p>
      </div>
      <div v-else class="grid-grafico-detalhes">
        <div class="container-donut">
          <div class="donut-wrapper">
            <Doughnut :key="mesSelecionado" :data="dadosDonut" :options="opcoesDonut" />
            <div class="centro-donut">
              <span class="label-centro">Total do Mês</span>
              <span class="valor-centro">{{ formatarMoeda(analiseFornecedoresMes.totalGeralMes) }}</span>
            </div>
          </div>
        </div>

        <div class="lista-fornecedores">
          <div 
            v-for="item in analiseFornecedoresMes.lista" 
            :key="item.distribuidora"
            class="item-fornecedor"
          >
            <div class="info-topo">
              <div class="nome-empresa">
                <span class="ponto-cor" :style="{ backgroundColor: item.cor, boxShadow: `0 0 8px ${item.cor}` }"></span>
                <strong>{{ item.distribuidora }}</strong>
              </div>
              <div class="valores-empresa">
                <span class="valor-texto">{{ formatarMoeda(item.valor) }}</span>
                <span class="porcentagem-texto">{{ item.porcentagem }}%</span>
              </div>
            </div>
            <div class="trilho-progresso">
              <div class="barra-progresso" :style="{ width: item.porcentagem + '%', backgroundColor: item.cor }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODO 2: BARRAS POR FORNECEDOR -->
    <div v-else-if="tipoGrafico === 'barras'" style="height: 290px;">
      <div v-if="analiseFornecedoresMes.lista.length === 0" class="estado-vazio">
        <div class="icone-vazio">✨</div>
        <p style="font-weight: 600; color: #f1f5f9;">Sem contas pendentes para este mês</p>
      </div>
      <Bar v-else :key="mesSelecionado" :data="dadosBarras" :options="opcoesGeraisCartesianas" />
    </div>

    <!-- MODO 3: LINHA DO TEMPO -->
    <div v-else-if="tipoGrafico === 'timeline'" style="height: 290px;">
      <div v-if="dadosLinhaDoTempo.labels.length === 0" class="estado-vazio">
        <div class="icone-vazio">✨</div>
        <p style="font-weight: 600; color: #f1f5f9;">Sem contas pendentes para projetar no calendário</p>
      </div>
      <Line v-else :data="dadosLinhaDoTempo" :options="opcoesGeraisCartesianas" />
    </div>
  </div>
</template>

<style scoped>
.card-grafico {
  background: #0f172a;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #1e293b;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  margin-bottom: 24px;
}

.header-grafico {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 24px;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 16px;
}

.titulo-secao {
  font-size: 18px;
  font-weight: 700;
  color: #f8fafc;
}

.subtitulo-secao {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

.controles-grafico {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.seletor-estilo-grafico {
  display: flex;
  background: #131c31;
  padding: 3px;
  border-radius: 8px;
  border: 1px solid #334155;
  gap: 2px;
}

.btn-tipo-grafico {
  padding: 5px 12px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-tipo-ativo {
  background: #1e293b;
  color: #00d2ff;
  box-shadow: 0 0 8px rgba(0, 210, 255, 0.15);
}

.seletor-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1e293b;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid #334155;
}

.label-seletor {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

.select-mes {
  border: 1px solid #334155;
  background: #0f172a;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #00d2ff;
  cursor: pointer;
  outline: none;
}

.grid-grafico-detalhes {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 30px;
  align-items: center;
}

@media (max-width: 800px) {
  .grid-grafico-detalhes {
    grid-template-columns: 1fr;
  }
}

.container-donut {
  display: flex;
  justify-content: center;
  align-items: center;
}

.donut-wrapper {
  position: relative;
  width: 240px;
  height: 240px;
}

.centro-donut {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.label-centro {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #94a3b8;
}

.valor-centro {
  display: block;
  font-size: 17px;
  font-weight: 800;
  color: #00d2ff;
  margin-top: 2px;
}

.lista-fornecedores {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-fornecedor {
  background: #131c31;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid #1e293b;
}

.info-topo {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.nome-empresa {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #f1f5f9;
}

.ponto-cor {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.valores-empresa {
  display: flex;
  align-items: center;
  gap: 12px;
}

.valor-texto {
  font-weight: 700;
  color: #f8fafc;
}

.porcentagem-texto {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  min-width: 45px;
  text-align: right;
}

.trilho-progresso {
  height: 6px;
  background: #1e293b;
  border-radius: 999px;
  overflow: hidden;
}

.barra-progresso {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.estado-vazio {
  text-align: center;
  padding: 40px 20px;
  background: #131c31;
  border-radius: 12px;
  border: 1px dashed #334155;
}

.icone-vazio {
  font-size: 32px;
  margin-bottom: 8px;
}
</style>