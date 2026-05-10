<!--
  智能问答 - 清爽风格
-->
<template>
  <div class="chat-page">
    <!-- 快捷问题 -->
    <div class="quick-section" v-if="messages.length === 0">
      <div class="quick-title">试试问这些问题</div>
      <div class="quick-grid">
        <div v-for="q in quickQuestions" :key="q" class="quick-card" @click="askQuick(q)">
          <span>→</span>
          <span>{{ q }}</span>
        </div>
      </div>
    </div>

    <div class="chat-layout">
      <!-- 左侧对话 -->
      <div class="chat-left">
        <div class="chat-messages" ref="messageListRef">
          <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">
            <div class="msg-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
            <div class="msg-body">
              <div class="msg-role">{{ msg.role === 'user' ? '你' : '知识引擎' }}</div>
              <div class="msg-text" style="white-space: pre-line;">{{ msg.text }}</div>
            </div>
          </div>

          <div v-if="loading" class="msg assistant">
            <div class="msg-avatar">AI</div>
            <div class="msg-body">
              <div class="msg-role">知识引擎</div>
              <div class="msg-text typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <input v-model="inputText" placeholder="输入问题..." @keyup.enter="sendMessage" :disabled="loading" />
          <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">发送</button>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="chat-right">
        <div class="panel-title">⚙ Agent 协同详情</div>

        <div v-if="agentSteps.length === 0" class="panel-empty">
          <p>发送问题后</p>
          <p>各 Agent 协同过程将在此展示</p>
        </div>

        <div v-else class="agent-flow">
          <div v-for="(step, idx) in agentSteps" :key="idx" class="agent-node">
            <div class="agent-connector" v-if="idx > 0"></div>
            <div :class="['agent-card', agentClass(step.agent_name)]">
              <div class="agent-header">
                <span class="agent-name">{{ step.agent_name }}</span>
                <span class="agent-badge">{{ step.status }}</span>
              </div>
              <div class="agent-output">{{ step.output }}</div>
            </div>
          </div>
        </div>

        <div v-if="relatedChunks.length > 0" style="margin-top: 16px;">
          <div class="panel-title">🔍 检索片段</div>
          <div v-for="(chunk, idx) in relatedChunks" :key="idx" class="chunk-row">
            <span class="chunk-tag">#{{ idx + 1 }}</span>
            <span class="chunk-body">{{ chunk.substring(0, 100) }}...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

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
.chat-page { display: flex; flex-direction: column; gap: 16px; height: calc(100vh - 110px); }

.quick-section { text-align: center; padding: 16px 0; }
.quick-title { font-size: 13px; color: #86909c; margin-bottom: 12px; }
.quick-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-width: 560px; margin: 0 auto; }
.quick-card {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; background: #fff; border: 1px solid #e5e6eb;
  border-radius: 8px; cursor: pointer; font-size: 13px; color: #4e5969;
  transition: all 0.2s;
}
.quick-card:hover { border-color: #165dff; color: #165dff; }

.chat-layout { display: flex; gap: 14px; flex: 1; min-height: 0; }

.chat-left {
  flex: 1; display: flex; flex-direction: column;
  background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; overflow: hidden;
}

.chat-right {
  width: 320px; flex-shrink: 0;
  background: #fff; border: 1px solid #e5e6eb; border-radius: 10px;
  padding: 16px; overflow-y: auto;
}

.chat-right::-webkit-scrollbar { width: 4px; }
.chat-right::-webkit-scrollbar-thumb { background: #c9cdd4; border-radius: 2px; }

/* 消息 */
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; }
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: #c9cdd4; border-radius: 2px; }

.msg { display: flex; gap: 10px; margin-bottom: 16px; }
.msg.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.msg.user .msg-avatar { background: #165dff; color: #fff; }
.msg.assistant .msg-avatar { background: #e8f3ff; color: #165dff; }

.msg-body { max-width: 75%; }
.msg-role { font-size: 11px; color: #86909c; margin-bottom: 3px; }
.msg.user .msg-role { text-align: right; }

.msg-text {
  padding: 10px 14px; border-radius: 10px; font-size: 14px; line-height: 1.7;
}
.msg.user .msg-text { background: #165dff; color: #fff; }
.msg.assistant .msg-text { background: #f7f8fa; color: #1d2129; }

/* 打字动画 */
.typing-dots { display: flex; gap: 5px; padding: 14px 18px; }
.typing-dots span {
  width: 7px; height: 7px; background: #165dff; border-radius: 50%;
  animation: dotBounce 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.5); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入 */
.chat-input {
  display: flex; padding: 10px 14px; border-top: 1px solid #f2f3f5; gap: 8px;
}
.chat-input input {
  flex: 1; border: 1px solid #e5e6eb; border-radius: 8px;
  padding: 9px 14px; font-size: 14px; color: #1d2129; outline: none;
}
.chat-input input:focus { border-color: #165dff; }
.chat-input input::placeholder { color: #c9cdd4; }

.send-btn {
  padding: 0 20px; border-radius: 8px; border: none;
  background: #165dff; color: #fff; font-size: 14px; cursor: pointer;
}
.send-btn:hover:not(:disabled) { background: #4080ff; }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Agent 面板 */
.panel-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }
.panel-empty { text-align: center; padding: 32px 0; color: #c9cdd4; font-size: 13px; }

.agent-flow { display: flex; flex-direction: column; }

.agent-connector { width: 2px; height: 10px; background: #e5e6eb; margin-left: 16px; }

.agent-card {
  padding: 10px 12px; border-radius: 8px;
  background: #fafafa; border: 1px solid #f2f3f5;
  border-left: 3px solid #c9cdd4;
}
.agent-card.ctrl { border-left-color: #ff7d00; }
.agent-card.search { border-left-color: #165dff; }
.agent-card.topo { border-left-color: #52c41a; }
.agent-card.summary { border-left-color: #722ed1; }

.agent-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.agent-name { font-size: 13px; font-weight: 600; color: #1d2129; }
.agent-badge { font-size: 10px; padding: 1px 6px; border-radius: 3px; background: #e8ffea; color: #00a870; margin-left: auto; }
.agent-output { font-size: 12px; color: #4e5969; line-height: 1.5; }

.chunk-row { display: flex; gap: 8px; padding: 6px 8px; background: #fafafa; border-radius: 5px; margin-bottom: 5px; }
.chunk-tag { font-size: 11px; font-weight: 700; color: #165dff; flex-shrink: 0; }
.chunk-body { font-size: 12px; color: #86909c; }
</style>
