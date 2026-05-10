<template>
  <div class="doc-page">
    <!-- 统计卡片 -->
    <div class="stat-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-value">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 上传区 -->
    <div class="section-card">
      <div class="section-title">文档上传</div>
      <el-upload
        drag action="/api/upload"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :before-upload="beforeUpload"
        accept=".pdf,.docx,.doc,.txt"
        class="upload-area"
      >
        <div class="upload-inner">
          <div class="upload-icon">↑</div>
          <div class="upload-text">拖拽文件到此处，或 <em>点击上传</em></div>
          <div class="upload-hint">支持 PDF / Word / TXT</div>
        </div>
      </el-upload>
    </div>

    <!-- 处理流水线 -->
    <div class="section-card" v-if="parsedChunks.length > 0">
      <div class="section-title">处理流水线</div>
      <div class="pipeline">
        <div class="step done">
          <div class="step-circle">✓</div>
          <div class="step-line"></div>
          <div class="step-content">
            <div class="step-name">文档解析</div>
            <div class="step-desc">{{ uploadResult?.chunk_count || 0 }} 个切片已就绪</div>
          </div>
        </div>
        <div class="step" :class="{ done: extractResult, active: !extractResult }">
          <div class="step-circle">{{ extractResult ? '✓' : '2' }}</div>
          <div class="step-content">
            <div class="step-name">实体抽取</div>
            <div class="step-desc">{{ extractResult ? `${extractResult.entity_count} 实体 / ${extractResult.relation_count} 关系` : '提取人员、部门、系统等实体' }}</div>
          </div>
          <el-button v-if="!extractResult" type="warning" size="small" @click="extractEntities" :loading="extracting">开始抽取</el-button>
        </div>
        <div class="step" :class="{ done: embedResult, active: extractResult && !embedResult }">
          <div class="step-circle">{{ embedResult ? '✓' : '3' }}</div>
          <div class="step-content">
            <div class="step-name">向量入库</div>
            <div class="step-desc">{{ embedResult ? `${embedResult.embedded_count} 条向量已入库` : '文本转向量存入检索库' }}</div>
          </div>
          <el-button v-if="!embedResult && extractResult" type="warning" size="small" @click="embedDocument" :loading="embedding">开始入库</el-button>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="section-card" v-if="docList.length > 0">
      <div class="section-title">文档库</div>
      <div class="doc-grid">
        <div class="doc-card" v-for="doc in docList" :key="doc.filename">
          <div class="doc-icon">{{ fileIcon(doc.file_type) }}</div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.filename }}</div>
            <div class="doc-meta">{{ doc.file_type.toUpperCase() }} · {{ doc.total_length }} 字 · {{ doc.chunk_count }} 片</div>
          </div>
          <button class="doc-delete" @click="deleteDocument(doc.filename)">×</button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <EmptyState
      v-if="docList.length === 0 && !uploadResult"
      icon="◈"
      title="暂无文档"
      description="上传 PDF、Word 或 TXT 文件开始使用"
    />

    <!-- 实体关系结果 -->
    <div class="section-card" v-if="extractResult">
      <div class="section-title">知识抽取结果</div>
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="sub-title">实体 ({{ extractResult.entity_count }})</div>
          <el-table :data="extractResult.entities" size="small" max-height="220">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="entity_type" label="类型" />
          </el-table>
        </el-col>
        <el-col :span="12">
          <div class="sub-title">关系 ({{ extractResult.relation_count }})</div>
          <el-table :data="extractResult.relations" size="small" max-height="220">
            <el-table-column prop="source" label="源实体" />
            <el-table-column prop="relation_type" label="关系" />
            <el-table-column prop="target" label="目标" />
          </el-table>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import EmptyState from './EmptyState.vue'

const uploadResult = ref(null)
const extractResult = ref(null)
const embedResult = ref(null)
const parsedChunks = ref([])
const docList = ref([])
const extracting = ref(false)
const embedding = ref(false)

const stats = computed(() => [
  { label: '已上传文档', value: docList.value.length },
  { label: '文本切片', value: docList.value.reduce((s, d) => s + d.chunk_count, 0) },
  { label: '知识实体', value: extractResult.value?.entity_count || 0 },
  { label: '实体关系', value: extractResult.value?.relation_count || 0 },
])

function fileIcon(type) {
  const icons = { pdf: '◇', docx: '◈', doc: '◈', txt: '□' }
  return icons[type] || '○'
}

function beforeUpload(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['pdf', 'docx', 'doc', 'txt'].includes(ext)) {
    ElMessage.error('仅支持 PDF / Word / TXT')
    return false
  }
  return true
}

function onUploadSuccess(res) {
  uploadResult.value = res
  parsedChunks.value = res.chunks
  extractResult.value = null
  embedResult.value = null
  ElMessage.success(`解析完成，${res.chunk_count} 个切片`)
  loadDocList()
}

function onUploadError() { ElMessage.error('上传失败') }

async function extractEntities() {
  extracting.value = true
  try {
    const res = await fetch('/api/extract', { method: 'POST' })
    const data = await res.json()
    extractResult.value = data
    ElMessage.success(`抽取完成：${data.entity_count} 实体`)
  } catch (e) { ElMessage.error('抽取失败') }
  finally { extracting.value = false }
}

async function embedDocument() {
  embedding.value = true
  try {
    const res = await fetch('/api/embed?doc_name=' + (uploadResult.value?.filename || 'default'), { method: 'POST' })
    const data = await res.json()
    embedResult.value = data
    ElMessage.success(`入库完成：${data.embedded_count} 条`)
  } catch (e) { ElMessage.error('入库失败') }
  finally { embedding.value = false }
}

async function loadDocList() {
  try {
    const res = await fetch('/api/docs')
    const data = await res.json()
    docList.value = data.documents || []
  } catch (e) { /* ignore */ }
}

async function deleteDocument(filename) {
  try {
    const res = await fetch(`/api/docs/${encodeURIComponent(filename)}`, { method: 'DELETE' })
    if (!res.ok) { ElMessage.error('删除失败'); return }
    ElMessage.success(`已删除：${filename}`)
    loadDocList()
  } catch (e) { ElMessage.error('删除失败') }
}

onMounted(() => loadDocList())
</script>

<style scoped>
.doc-page { display: flex; flex-direction: column; gap: 20px; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 20px; text-align: center;
  transition: all var(--transition-fast);
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--accent);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 28px; font-weight: 800;
  color: var(--accent);
  letter-spacing: -1px;
}

.stat-label {
  font-size: 12px; color: var(--text-muted);
  margin-top: 4px; font-weight: 500;
}

.upload-area { width: 100%; }
.upload-inner { padding: 32px; text-align: center; }

.upload-icon {
  font-size: 36px; color: var(--text-muted);
  margin-bottom: 8px; opacity: 0.5;
}

.upload-text { color: var(--text-secondary); font-size: 14px; }
.upload-text em {
  color: var(--accent); font-style: normal;
  font-weight: 600;
}
.upload-hint {
  color: var(--text-muted); font-size: 12px;
  margin-top: 4px;
}

.pipeline { display: flex; flex-direction: column; gap: 0; }

.step {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 0; position: relative;
}

.step:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 15px; top: 42px;
  width: 2px; height: calc(100% - 28px);
  background: var(--border);
}

.step.done:not(:last-child)::after { background: var(--green); }

.step-circle {
  width: 32px; height: 32px; flex-shrink: 0;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-size: 13px; font-weight: 600;
  background: var(--bg-hover);
  color: var(--text-muted);
  border: 2px solid var(--border);
  position: relative; z-index: 1;
  transition: all var(--transition-normal);
}

.step.done .step-circle {
  background: var(--green);
  color: #fff;
  border-color: var(--green);
}

.step.active .step-circle {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  animation: stepPulse 2s ease-in-out infinite;
}

@keyframes stepPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.3); }
  50% { box-shadow: 0 0 0 8px rgba(245,158,11,0); }
}

.step-content { flex: 1; min-width: 0; }
.step-name { font-weight: 600; font-size: 14px; color: var(--text-primary); }
.step-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.step .el-button { margin-left: auto; flex-shrink: 0; }

.doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }

.doc-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.doc-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-xs);
}

.doc-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  background: var(--accent-soft);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: var(--accent);
}

.doc-info { flex: 1; min-width: 0; }
.doc-name {
  font-size: 13px; font-weight: 600;
  color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.doc-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; font-family: var(--font-mono); }

.doc-delete {
  background: none; border: none; cursor: pointer;
  font-size: 18px; color: var(--text-muted);
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-fast);
}
.doc-delete:hover { background: rgba(239,68,68,0.1); color: var(--red); }

.sub-title {
  font-size: 13px; font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .doc-grid { grid-template-columns: 1fr; }
}
</style>
