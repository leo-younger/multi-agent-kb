<!--
  知识图谱 - 3D 立体效果 + 人物头像
-->
<template>
  <div class="graph-page">
    <div class="graph-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">🔗 知识图谱</span>
        <span class="toolbar-info" v-if="graphData">{{ graphData.nodes.length }} 节点 / {{ graphData.edges.length }} 关系</span>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="toggleLabels">{{ showLabels ? '隐藏标签' : '显示标签' }}</el-button>
        <el-button size="small" @click="loadGraph" :loading="loading">刷新</el-button>
      </div>
    </div>

    <div class="graph-container" ref="containerRef">
      <div ref="chartRef" class="chart-area"></div>
      <!-- 图例 -->
      <div class="legend-bar">
        <div class="legend-item">
          <span class="legend-icon person-icon"></span>
          <span>人员</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon dept-icon"></span>
          <span>部门</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon sys-icon"></span>
          <span>系统</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon mod-icon"></span>
          <span>模块</span>
        </div>
        <div class="legend-item">
          <span class="legend-icon api-icon"></span>
          <span>接口</span>
        </div>
      </div>
      <!-- 详情浮层 -->
      <div class="detail-popup" v-if="selectedNode" :style="popupStyle">
        <div class="popup-close" @click="selectedNode = null">×</div>
        <div class="popup-avatar" :style="{ background: selectedNode.color }">
          <span>{{ selectedNode.name[0] }}</span>
        </div>
        <div class="popup-info">
          <div class="popup-name">{{ selectedNode.name }}</div>
          <div class="popup-type">{{ selectedNode.type }}</div>
          <div class="popup-rels" v-if="selectedNode.relations.length > 0">
            <div v-for="r in selectedNode.relations" :key="r.text" class="popup-rel">{{ r.text }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const containerRef = ref(null)
const graphData = ref(null)
const loading = ref(false)
const showLabels = ref(true)
const selectedNode = ref(null)
const popupStyle = ref({})
let chart = null

// 各类型颜色
const categoryColors = {
  '人员': '#165dff',
  '部门': '#52c41a',
  '系统': '#ff7d00',
  '模块': '#722ed1',
  '接口': '#13c2c2',
}

// 人物头像颜色（每人不同）
const avatarColors = ['#165dff', '#722ed1', '#eb2f96', '#fa541c', '#faad14', '#13c2c2', '#2f54eb', '#a0d911']

// 人物头像 SVG（简约人形轮廓）
const personSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="__COLOR__" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="__COLOR2__" stop-opacity="0.7"/>
    </linearGradient>
    <filter id="s"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="__COLOR__" flood-opacity="0.4"/></filter>
  </defs>
  <circle cx="32" cy="32" r="30" fill="url(#g)" filter="url(#s)"/>
  <circle cx="32" cy="24" r="10" fill="rgba(255,255,255,0.9)"/>
  <ellipse cx="32" cy="48" rx="16" ry="12" fill="rgba(255,255,255,0.9)"/>
</svg>`

function getPersonImage(color) {
  const c2 = color + '99'
  const svg = personSvg.replace(/__COLOR__/g, color).replace('__COLOR2__', c2)
  return 'image://data:image/svg+xml,' + encodeURIComponent(svg)
}

// 部门图标
const deptSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#52c41a"/><stop offset="100%" stop-color="#389e0d"/></linearGradient></defs>
  <rect x="4" y="4" width="56" height="56" rx="12" fill="url(#g)"/>
  <rect x="14" y="20" width="10" height="26" rx="2" fill="rgba(255,255,255,0.85)"/>
  <rect x="27" y="14" width="10" height="32" rx="2" fill="rgba(255,255,255,0.85)"/>
  <rect x="40" y="22" width="10" height="24" rx="2" fill="rgba(255,255,255,0.85)"/>
</svg>`

// 系统图标
const sysSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ff7d00"/><stop offset="100%" stop-color="#d46b08"/></linearGradient></defs>
  <rect x="4" y="4" width="56" height="56" rx="8" fill="url(#g)"/>
  <rect x="14" y="14" width="14" height="14" rx="3" fill="rgba(255,255,255,0.85)"/>
  <rect x="36" y="14" width="14" height="14" rx="3" fill="rgba(255,255,255,0.85)"/>
  <rect x="14" y="36" width="14" height="14" rx="3" fill="rgba(255,255,255,0.85)"/>
  <rect x="36" y="36" width="14" height="14" rx="3" fill="rgba(255,255,255,0.85)"/>
</svg>`

// 模块图标
const modSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#722ed1"/><stop offset="100%" stop-color="#531dab"/></linearGradient></defs>
  <circle cx="32" cy="32" r="28" fill="url(#g)"/>
  <path d="M32 16 L20 40 H44 Z" fill="rgba(255,255,255,0.85)" stroke="none"/>
  <circle cx="32" cy="34" r="6" fill="url(#g)"/>
</svg>`

// 接口图标
const apiSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#13c2c2"/><stop offset="100%" stop-color="#08979c"/></linearGradient></defs>
  <polygon points="32,4 60,20 60,44 32,60 4,44 4,20" fill="url(#g)"/>
  <circle cx="32" cy="32" r="10" fill="rgba(255,255,255,0.85)"/>
</svg>`

function getSvgDataUri(svg) {
  return 'image://data:image/svg+xml,' + encodeURIComponent(svg)
}

function getNodeSymbol(category, index) {
  switch (category) {
    case '人员': return getPersonImage(avatarColors[index % avatarColors.length])
    case '部门': return getSvgDataUri(deptSvg)
    case '系统': return getSvgDataUri(sysSvg)
    case '模块': return getSvgDataUri(modSvg)
    case '接口': return getSvgDataUri(apiSvg)
    default: return 'circle'
  }
}

async function loadGraph() {
  loading.value = true
  try {
    const res = await fetch('/api/graph')
    const data = await res.json()
    graphData.value = data
    renderChart(data)
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function renderChart(data) {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const categories = []
  const seen = new Set()
  data.nodes.forEach(n => {
    if (!seen.has(n.category)) { seen.add(n.category); categories.push({ name: n.category }) }
  })

  // 为每个节点分配头像索引
  let personIdx = 0

  const categoryMap = new Map(categories.map((c, i) => [c.name, i]))

  const nodes = data.nodes.map(n => {
    const catIdx = categoryMap.get(n.category) ?? 0
    const isPerson = n.category === '人员'
    const pIdx = isPerson ? personIdx++ : 0
    const size = isPerson ? 60 : (n.category === '部门' ? 52 : 46)

    return {
      name: n.name,
      category: catIdx,
      symbolSize: size,
      symbol: getNodeSymbol(n.category, pIdx),
      itemStyle: {
        color: categoryColors[n.category] || '#86909c',
        shadowBlur: 20,
        shadowColor: (categoryColors[n.category] || '#86909c') + '60',
        shadowOffsetY: 6,
        borderColor: '#fff',
        borderWidth: 3,
      },
      label: {
        show: showLabels.value,
        position: 'bottom',
        distance: 8,
        color: '#1d2129',
        fontSize: 12,
        fontWeight: 600,
        backgroundColor: 'rgba(255,255,255,0.85)',
        padding: [3, 8],
        borderRadius: 4,
        shadowBlur: 4,
        shadowColor: 'rgba(0,0,0,0.08)',
        shadowOffsetY: 2,
      },
    }
  })

  const edges = data.edges.map(e => ({
    source: e.source,
    target: e.target,
    label: { show: false, formatter: e.label, fontSize: 10, color: '#4e5969' },
    lineStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: categoryColors[data.nodes.find(n => n.name === e.source)?.category] || '#c9cdd4' + '80' },
          { offset: 1, color: categoryColors[data.nodes.find(n => n.name === e.target)?.category] || '#c9cdd4' + '80' },
        ],
      },
      curveness: 0.15,
      width: 2,
      shadowBlur: 6,
      shadowColor: 'rgba(0,0,0,0.1)',
    },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e5e6eb',
      borderWidth: 1,
      padding: [12, 16],
      textStyle: { color: '#1d2129', fontSize: 13 },
      extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 10px;',
      formatter(p) {
        if (p.dataType === 'node') {
          const cat = categories[p.data.category]?.name || ''
          const color = categoryColors[cat] || '#86909c'
          return `<div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;">${p.name[0]}</div>
            <div><div style="font-weight:700;font-size:15px;">${p.name}</div><div style="color:#86909c;font-size:12px;margin-top:2px;">${cat}</div></div>
          </div>`
        }
        if (p.dataType === 'edge') {
          return `<div style="font-size:13px;"><b>${p.data.source}</b> <span style="color:#86909c;">→ ${p.data.label?.formatter || ''} →</span> <b>${p.data.target}</b></div>`
        }
        return ''
      },
    },
    legend: { show: false },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: edges,
      categories,
      roam: true,
      draggable: true,
      force: {
        repulsion: 600,
        edgeLength: [150, 280],
        gravity: 0.06,
        friction: 0.6,
      },
      label: { show: showLabels.value, position: 'bottom' },
      edgeLabel: { show: false },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4, color: '#165dff' },
        itemStyle: { shadowBlur: 30, borderWidth: 4 },
        label: { fontWeight: 700 },
      },
      blur: {
        itemStyle: { opacity: 0.15 },
        lineStyle: { opacity: 0.05 },
      },
      scaleLimit: { min: 0.5, max: 3 },
      animationDuration: 1200,
      animationEasingUpdate: 'quinticInOut',
    }],
  })

  // 点击节点显示详情
  chart.off('click')
  chart.on('click', (params) => {
    if (params.dataType !== 'node') { selectedNode.value = null; return }
    const nodeData = data.nodes.find(n => n.name === params.name)
    if (!nodeData) return
    const rels = data.edges
      .filter(e => e.source === params.name || e.target === params.name)
      .map(e => ({
        text: e.source === params.name
          ? `${e.label} → ${e.target}`
          : `${e.source} → ${e.label}`,
      }))
    selectedNode.value = {
      name: params.name,
      type: nodeData.category,
      color: categoryColors[nodeData.category] || '#86909c',
      relations: rels,
    }
    // 定位浮层
    if (containerRef.value && params.event) {
      const rect = containerRef.value.getBoundingClientRect()
      const x = params.event.offsetX
      const y = params.event.offsetY
      popupStyle.value = {
        left: Math.min(x + 20, rect.width - 260) + 'px',
        top: Math.min(y - 20, rect.height - 200) + 'px',
      }
    }
  })

  // 点击空白关闭浮层
  chart.getZr().on('click', (e) => {
    if (!e.target) selectedNode.value = null
  })
}

function toggleLabels() {
  showLabels.value = !showLabels.value
  if (chart) {
    chart.setOption({ series: [{ label: { show: showLabels.value } }] })
  }
}

function handleResize() { chart?.resize() }

onMounted(async () => {
  await nextTick(); loadGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.graph-page { display: flex; flex-direction: column; gap: 12px; height: calc(100vh - 110px); }

.graph-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; background: #fff; border: 1px solid #e5e6eb; border-radius: 8px;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; }
.toolbar-right { display: flex; gap: 8px; }
.toolbar-title { font-size: 14px; font-weight: 600; color: #1d2129; }
.toolbar-info { font-size: 12px; color: #86909c; background: #f7f8fa; padding: 2px 8px; border-radius: 4px; }

.graph-container {
  flex: 1; position: relative;
  background: linear-gradient(135deg, #f8faff 0%, #f0f5ff 50%, #f5f8ff 100%);
  border: 1px solid #e5e6eb; border-radius: 10px; overflow: hidden;
}

.chart-area { width: 100%; height: 100%; }

/* 图例 */
.legend-bar {
  position: absolute; bottom: 14px; left: 14px;
  display: flex; gap: 14px; padding: 8px 16px;
  background: rgba(255,255,255,0.92); border: 1px solid #e5e6eb;
  border-radius: 8px; backdrop-filter: blur(8px);
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #4e5969; }
.legend-icon { width: 14px; height: 14px; border-radius: 50%; }
.person-icon { background: #165dff; }
.dept-icon { background: #52c41a; border-radius: 3px; }
.sys-icon { background: #ff7d00; border-radius: 3px; }
.mod-icon { background: #722ed1; }
.api-icon { background: #13c2c2; border-radius: 2px; transform: rotate(45deg); }

/* 详情浮层 */
.detail-popup {
  position: absolute; z-index: 10;
  width: 240px; padding: 16px;
  background: rgba(255,255,255,0.96);
  border: 1px solid #e5e6eb; border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.12);
  backdrop-filter: blur(12px);
  animation: popupIn 0.2s ease-out;
}

@keyframes popupIn {
  from { opacity: 0; transform: translateY(8px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.popup-close {
  position: absolute; top: 8px; right: 12px;
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #86909c; cursor: pointer;
  transition: all 0.2s;
}
.popup-close:hover { background: #f2f3f5; color: #1d2129; }

.popup-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 20px; font-weight: 800;
  margin-bottom: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.popup-name { font-size: 16px; font-weight: 700; color: #1d2129; }
.popup-type { font-size: 12px; color: #86909c; margin-top: 2px; }

.popup-rels { margin-top: 10px; border-top: 1px solid #f2f3f5; padding-top: 8px; }
.popup-rel {
  font-size: 12px; color: #4e5969; padding: 3px 0;
  display: flex; align-items: center; gap: 4px;
}
.popup-rel::before {
  content: ''; width: 4px; height: 4px; border-radius: 50%;
  background: #165dff; flex-shrink: 0;
}
</style>
