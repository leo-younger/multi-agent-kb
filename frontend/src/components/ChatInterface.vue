<template>
  <div class="chat-page">
    <!-- 快捷问题 -->
    <div class="quick-section" v-if="messages.length === 0">
      <div class="quick-title">试试问这些问题</div>
      <div class="quick-grid">
        <div v-for="(q, i) in quickQuestions" :key="q" class="quick-card" @click="askQuick(q)" :style="{ animationDelay: i * 80 + 'ms' }">
          <span class="quick-num">{{ String(i + 1).padStart(2, '0') }}</span>
          <span>{{ q }}</span>
        </div>
      </div>
    </div>

    <div class="chat-layout">
      <!-- 左侧对话 -->
      <div class="chat-left">
        <div class="chat-messages" ref="messageListRef">
          <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">
            <div class="msg-avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
            <div class="msg-body">
              <div class="msg-text" style="white-space: pre-line;">{{ msg.text }}</div>
            </div>
          </div>

          <div v-if="loading" class="msg assistant">
            <div class="msg-avatar">AI</div>
            <div class="msg-body">
              <div class="msg-text typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <EmptyState
            v-if="messages.length === 0 && !loading"
            icon="◉"
            title="输入问题开始探索知识库"
            description="基于已上传的文档和知识图谱进行智能问答"
          />
        </div>

        <div class="chat-input">
          <input v-model="inputText" placeholder="输入问题..." @keyup.enter="sendMessage" :disabled="loading" />
          <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
            →
          </button>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="chat-right">
        <div class="panel-header">
          <span class="panel-title">Agent 协同详情</span>
          <span class="panel-badge" v-if="agentSteps.length > 0">{{ agentSteps.length }} 步</span>
        </div>

        <div v-if="agentSteps.length === 0" class="panel-empty">
          <div class="empty-hint">发送问题后</div>
          <div class="empty-hint">各 Agent 协同过程将在此展示</div>
        </div>

        <div v-else class="agent-timeline">
          <div v-for="(step, idx) in agentSteps" :key="idx" class="timeline-item">
            <div class="timeline-dot" :class="agentClass(step.agent_name)"></div>
            <div v-if="idx < agentSteps.length - 1" class="timeline-line"></div>
            <div class="timeline-card">
              <div class="timeline-header">
                <span class="timeline-name">{{ step.agent_name }}</span>
                <span class="timeline-status">{{ step.status }}</span>
              </div>
              <div class="timeline-output">{{ step.output }}</div>
            </div>
          </div>
        </div>

        <div v-if="relatedChunks.length > 0" class="chunks-section">
          <div class="panel-header">
            <span class="panel-title">检索片段</span>
          </div>
          <div v-for="(chunk, idx) in relatedChunks" :key="idx" class="chunk-card">
            <span class="chunk-num">#{{ idx + 1 }}</span>
            <span class="chunk-text">{{ chunk.substring(0, 100) }}...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import EmptyState from './EmptyState.vue'

const inputText = ref('')
const messages = ref([])
const agentSteps = ref([])
const relatedChunks = ref([])
const loading = ref(false)
const messageListRef = ref(null)

const quickQuestions = [
  '张三负责什么模块？',
  '知识库模块依赖哪些服务？',
  '技术部管理哪些系统？',
  '订单系统和用户系统有什么关系？',
]

function askQuick(q) { inputText.value = q; sendMessage() }

async function sendMessage() {
  const question = inputText.value.trim()
  if (!question) return
  messages.value.push({ role: 'user', text: question })
  inputText.value = ''
  loading.value = true
  agentSteps.value = []
  relatedChunks.value = []
  await nextTick(); scrollToBottom()

  try {
    const res = await fetch('/api/chat?question=' + encodeURIComponent(question), { method: 'POST' })
    const data = await res.json()
    messages.value.push({ role: 'assistant', text: data.answer })
    agentSteps.value = data.agent_steps || []
    relatedChunks.value = data.related_chunks || []
  } catch (e) {
    messages.value.push({ role: 'assistant', text: '请求失败：' + e.message })
    ElMessage.error('问答失败')
  } finally {
    loading.value = false
    await nextTick(); scrollToBottom()
  }
}

function scrollToBottom() {
  if (messageListRef.value) messageListRef.value.scrollTop = messageListRef.value.scrollHeight
}

function agentClass(name) {
  return { '总控Agent': 'ctrl', '检索Agent': 'search', '拓扑Agent': 'topo', '总结Agent': 'summary' }[name] || ''
}
</script>

<style scoped>
.chat-page { display: flex; flex-direction: column; gap: 16px; height: calc(100vh - var(--topbar-height) - 48px); }

.quick-section { text-align: center; padding: 20px 0; }
.quick-title {
  font-family: var(--font-display);
  font-size: 13px; color: var(--text-muted);
  margin-bottom: 14px; font-weight: 500;
}

.quick-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-width: 560px; margin: 0 auto; }

.quick-card {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer; font-size: 13px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  animation: cardFadeIn 0.4s ease both;
}

.quick-card:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.quick-num {
  font-family: var(--font-mono);
  font-size: 11px; font-weight: 600;
  color: var(--accent); opacity: 0.6;
}

@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-layout { display: flex; gap: 16px; flex: 1; min-height: 0; }

.chat-left {
  flex: 1; display: flex; flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.chat-right {
  width: 340px; flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 20px; overflow-y: auto;
}

.chat-right::-webkit-scrollbar { width: 4px; }
.chat-right::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px;
  display: flex; flex-direction: column;
}
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.msg { display: flex; gap: 12px; margin-bottom: 16px; }
.msg.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 32px; height: 32px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
  font-family: var(--font-mono);
}

.msg.user .msg-avatar {
  background: linear-gradient(135deg, var(--accent), #f97316);
  color: #fff;
}

.msg.assistant .msg-avatar {
  background: var(--bg-hover);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.msg-body { max-width: 75%; }

.msg-text {
  padding: 12px 16px; border-radius: var(--radius-md);
  font-size: 14px; line-height: 1.7;
}

.msg.user .msg-text {
  background: linear-gradient(135deg, var(--accent), #f97316);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .msg-text {
  background: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
}

.typing-dots { display: flex; gap: 6px; padding: 14px 18px; }
.typing-dots span {
  width: 6px; height: 6px;
  background: var(--accent); border-radius: 50%;
  animation: dotBounce 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.5); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input {
  display: flex; padding: 12px 16px;
  border-top: 1px solid var(--border-light);
  gap: 10px;
}

.chat-input input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 16px;
  font-size: 14px;
  font-family: var(--font-body);
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  transition: all var(--transition-fast);
}

.chat-input input:focus {
  border-color: var(--accent);
  box-shadow: 0 2px 0 var(--accent);
}

.chat-input input::placeholder { color: var(--text-muted); }

.send-btn {
  width: 40px; height: 40px;
  border-radius: var(--radius-sm); border: none;
  background: linear-gradient(135deg, var(--accent), #f97316);
  color: #fff; font-size: 18px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-fast);
}

.send-btn:hover:not(:disabled) { transform: scale(1.05); box-shadow: var(--shadow-glow); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 13px; font-weight: 700;
  color: var(--text-primary);
}

.panel-badge {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 600;
  padding: 2px 8px; border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
}

.panel-empty { text-align: center; padding: 40px 0; }
.empty-hint { font-size: 13px; color: var(--text-muted); line-height: 1.6; }

.agent-timeline { display: flex; flex-direction: column; }

.timeline-item {
  display: flex; gap: 12px;
  position: relative;
  padding-bottom: 16px;
}

.timeline-item:last-child { padding-bottom: 0; }

.timeline-dot {
  width: 10px; height: 10px; flex-shrink: 0;
  border-radius: 50%; margin-top: 6px;
  position: relative; z-index: 1;
  background: var(--border);
}

.timeline-dot.ctrl { background: var(--accent); }
.timeline-dot.search { background: var(--blue); }
.timeline-dot.topo { background: var(--green); }
.timeline-dot.summary { background: var(--purple); }

.timeline-line {
  position: absolute;
  left: 4px; top: 16px;
  width: 2px; height: calc(100% - 10px);
  background: var(--border);
}

.timeline-card {
  flex: 1; min-width: 0;
  padding: 10px 12px;
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--border);
}

.timeline-item:first-child .timeline-card { border-left-color: var(--accent); }
.timeline-item:nth-child(2) .timeline-card { border-left-color: var(--blue); }
.timeline-item:nth-child(3) .timeline-card { border-left-color: var(--green); }
.timeline-item:nth-child(4) .timeline-card { border-left-color: var(--purple); }

.timeline-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.timeline-name { font-size: 12px; font-weight: 700; color: var(--text-primary); }
.timeline-status {
  font-family: var(--font-mono);
  font-size: 10px; padding: 1px 6px;
  border-radius: 3px;
  background: rgba(16,185,129,0.1);
  color: var(--green);
  margin-left: auto;
}

.timeline-output { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }

.chunks-section { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border-light); }

.chunk-card {
  display: flex; gap: 10px;
  padding: 10px 12px;
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

.chunk-num {
  font-family: var(--font-mono);
  font-size: 11px; font-weight: 700;
  color: var(--accent); flex-shrink: 0;
}

.chunk-text { font-size: 12px; color: var(--text-muted); line-height: 1.5; }

@media (max-width: 1024px) {
  .chat-right { display: none; }
}
</style>
