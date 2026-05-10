# 前端界面重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 multi-agent-kb 前端重构为 "Editorial Intelligence" 风格——Bloomberg Terminal 遇上 Notion 的高端商务风，支持深浅色切换、页面动效、响应式布局。

**Architecture:** 渐进式重构，保留 Vue3 + Element Plus。新增 CSS 变量系统管理主题，新增 2 个通用组件（SkeletonLoader、EmptyState），重构 3 个页面组件 + App.vue 壳。

**Tech Stack:** Vue 3, Element Plus, ECharts 5, CSS Variables, Google Fonts (DM Sans + IBM Plex Sans + JetBrains Mono)

---

### Task 1: 设计系统 + 主题切换基础设施

**Files:**
- Create: `frontend/src/composables/useTheme.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/index.html`

- [ ] **Step 1: 在 index.html 引入 Google Fonts**

在 `<head>` 中添加字体链接：
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

- [ ] **Step 2: 创建 useTheme composable**

```javascript
// frontend/src/composables/useTheme.js
import { ref, watch } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
  }

  watch(theme, (val) => {
    document.documentElement.dataset.theme = val
  }, { immediate: true })

  return { theme, toggleTheme }
}
```

- [ ] **Step 3: 重写 App.vue 全局样式（CSS 变量 + 布局）**

替换整个 `<style>` 部分为设计系统变量 + 布局样式。完整代码见下方：

```vue
<!-- App.vue 完整重写 -->
<template>
  <div class="app-root">
    <div class="layout">
      <aside :class="['sidebar', { collapsed: sidebarCollapsed }]">
        <div class="logo-area">
          <div class="logo-mark">KB</div>
          <div v-show="!sidebarCollapsed" class="logo-text">
            <h1>知识引擎</h1>
            <p>多智能体协同</p>
          </div>
        </div>

        <nav class="nav-menu">
          <div
            v-for="item in navItems"
            :key="item.key"
            :class="['nav-item', { active: activeTab === item.key }]"
            @click="activeTab = item.key"
            :title="sidebarCollapsed ? item.label : ''"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          </div>
        </nav>

        <div class="sidebar-footer">
          <div class="status-indicator">
            <span class="pulse-dot"></span>
            <span v-show="!sidebarCollapsed">系统运行中</span>
          </div>
        </div>
      </aside>

      <main class="content">
        <header class="topbar">
          <div class="topbar-left">
            <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
              {{ sidebarCollapsed ? '☰' : '✕' }}
            </button>
            <span class="page-title">{{ currentNav?.label }}</span>
          </div>
          <div class="topbar-right">
            <div class="tech-badges">
              <span class="badge">Neo4j</span>
              <span class="badge accent">FastAPI</span>
              <span class="badge warm">Vue3</span>
            </div>
            <button class="theme-toggle" @click="toggleTheme">
              {{ theme === 'light' ? '☾' : '☀' }}
            </button>
          </div>
        </header>

        <div class="content-body">
          <Transition name="page" mode="out-in">
            <DocumentManager v-if="activeTab === 'docs'" />
            <ChatInterface v-else-if="activeTab === 'chat'" />
            <KnowledgeGraph v-else-if="activeTab === 'graph'" />
          </Transition>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from './composables/useTheme'
import DocumentManager from './components/DocumentManager.vue'
import ChatInterface from './components/ChatInterface.vue'
import KnowledgeGraph from './components/KnowledgeGraph.vue'

const { theme, toggleTheme } = useTheme()
const activeTab = ref('docs')
const sidebarCollapsed = ref(false)

const navItems = [
  { key: 'docs', label: '文档管理', icon: '◈' },
  { key: 'chat', label: '智能问答', icon: '◉' },
  { key: 'graph', label: '知识图谱', icon: '⬡' },
]

const currentNav = computed(() => navItems.find(n => n.key === activeTab.value))
</script>

<style>
/* ========== 设计系统变量 ========== */
:root {
  /* 亮色主题 */
  --bg-page: #f8f9fb;
  --bg-card: #ffffff;
  --bg-elevated: #ffffff;
  --bg-hover: #f1f3f5;
  --bg-active: #fff8e1;
  --bg-sidebar: #ffffff;
  --bg-topbar: rgba(255,255,255,0.85);
  --bg-input: #f8f9fb;

  --text-primary: #0f0f1a;
  --text-secondary: #5a5a72;
  --text-muted: #9a9ab0;
  --text-inverse: #ffffff;

  --border: #e8e8ee;
  --border-light: #f0f0f5;

  --accent: #f59e0b;
  --accent-hover: #d97706;
  --accent-soft: #fef3c7;
  --accent-glow: rgba(245,158,11,0.15);

  --blue: #3b82f6;
  --green: #10b981;
  --red: #ef4444;
  --purple: #8b5cf6;

  --shadow-xs: 0 1px 2px rgba(15,15,26,0.04);
  --shadow-sm: 0 2px 8px rgba(15,15,26,0.06);
  --shadow-md: 0 4px 16px rgba(15,15,26,0.08);
  --shadow-lg: 0 8px 32px rgba(15,15,26,0.12);
  --shadow-glow: 0 0 20px rgba(245,158,11,0.1);

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  --font-display: 'DM Sans', -apple-system, sans-serif;
  --font-body: 'IBM Plex Sans', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);

  --sidebar-width: 220px;
  --sidebar-collapsed: 64px;
  --topbar-height: 56px;
}

[data-theme="dark"] {
  --bg-page: #0a0a14;
  --bg-card: #12121f;
  --bg-elevated: #1a1a2e;
  --bg-hover: #1e1e32;
  --bg-active: #2a2000;
  --bg-sidebar: #0e0e1a;
  --bg-topbar: rgba(14,14,26,0.9);
  --bg-input: #16162a;

  --text-primary: #e8e8f0;
  --text-secondary: #9a9ab0;
  --text-muted: #5a5a72;
  --text-inverse: #0f0f1a;

  --border: #2a2a40;
  --border-light: #1e1e32;

  --accent-soft: #2a2000;
  --accent-glow: rgba(245,158,11,0.2);

  --shadow-xs: 0 1px 2px rgba(0,0,0,0.2);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
  --shadow-glow: 0 0 30px rgba(245,158,11,0.15);
}

/* ========== 全局重置 ========== */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-body);
  background: var(--bg-page);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

#app { height: 100vh; }

/* ========== 布局 ========== */
.app-root { height: 100vh; }
.layout { display: flex; height: 100vh; }

/* ========== 侧边栏 ========== */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  transition: width var(--transition-normal);
  overflow: hidden;
  position: relative;
  z-index: 10;
}

.sidebar.collapsed { width: var(--sidebar-collapsed); }

/* 侧边栏装饰线 */
.sidebar::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 1px; height: 100%;
  background: linear-gradient(to bottom, transparent, var(--accent) 50%, transparent);
  opacity: 0.3;
}

.logo-area {
  display: flex; align-items: center; gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid var(--border-light);
}

.logo-mark {
  width: 40px; height: 40px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), #f97316);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-family: var(--font-display);
  font-size: 14px; font-weight: 800; letter-spacing: 2px;
  box-shadow: var(--shadow-glow);
}

.logo-text h1 {
  font-family: var(--font-display);
  font-size: 15px; font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.logo-text p {
  font-size: 11px; color: var(--text-muted);
  margin-top: 1px; white-space: nowrap;
}

/* 导航 */
.nav-menu { flex: 1; padding: 12px 8px; }

.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: var(--radius-sm);
  cursor: pointer; font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  margin-bottom: 2px;
  position: relative;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-active);
  color: var(--accent);
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute; left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 60%;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
}

.nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
.nav-label { white-space: nowrap; }

/* 底部状态 */
.sidebar-footer {
  padding: 16px; border-top: 1px solid var(--border-light);
}

.status-indicator {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--text-muted);
}

.pulse-dot {
  width: 8px; height: 8px; flex-shrink: 0;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
  50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(16,185,129,0); }
}

/* ========== 内容区 ========== */
.content {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0; height: 100vh; overflow: hidden;
}

/* ========== 顶栏 ========== */
.topbar {
  height: var(--topbar-height);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-topbar);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}

.topbar-left { display: flex; align-items: center; gap: 16px; }
.topbar-right { display: flex; align-items: center; gap: 16px; }

.collapse-btn {
  background: none; border: none; cursor: pointer;
  font-size: 18px; color: var(--text-secondary);
  padding: 4px 8px; border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.collapse-btn:hover { background: var(--bg-hover); color: var(--text-primary); }

.page-title {
  font-family: var(--font-display);
  font-size: 16px; font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.tech-badges { display: flex; gap: 6px; }

.badge {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  padding: 3px 10px; border-radius: 20px;
  background: var(--bg-hover);
  color: var(--text-muted);
  border: 1px solid var(--border);
  letter-spacing: 0.5px;
}

.badge.accent {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: transparent;
}

.badge.warm {
  background: rgba(139,92,246,0.1);
  color: var(--purple);
  border-color: transparent;
}

.theme-toggle {
  background: none; border: 1px solid var(--border);
  cursor: pointer; font-size: 16px;
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-fast);
  color: var(--text-secondary);
}
.theme-toggle:hover {
  background: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent);
}

/* ========== 内容区 ========== */
.content-body {
  flex: 1; overflow-y: auto; padding: 24px;
  background: var(--bg-page);
}

.content-body::-webkit-scrollbar { width: 6px; }
.content-body::-webkit-scrollbar-thumb {
  background: var(--border); border-radius: 3px;
}
.content-body::-webkit-scrollbar-track { background: transparent; }

/* ========== 页面切换动效 ========== */
.page-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-enter-from {
  opacity: 0; transform: translateY(12px);
}
.page-leave-to {
  opacity: 0; transform: translateY(-8px);
}

/* ========== 通用卡片 ========== */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 24px;
  margin-bottom: 20px;
  transition: box-shadow var(--transition-fast);
}

.section-card:hover { box-shadow: var(--shadow-sm); }

.section-title {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20px;
  letter-spacing: -0.2px;
}

.section-title::before {
  content: '';
  width: 3px; height: 16px;
  background: var(--accent);
  border-radius: 2px;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .content-body { padding: 16px; }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar { width: var(--sidebar-collapsed); }
  .nav-label, .logo-text, .sidebar-footer span { display: none; }
}
</style>
```

- [ ] **Step 4: 验证**

启动前端 `npm run dev`，确认：
1. 页面正常显示，字体加载
2. 点击顶栏月亮图标可切换深浅色
3. 点击折叠按钮侧边栏收起/展开
4. 三个页面切换有淡入淡出效果

- [ ] **Step 5: Commit**

```bash
cd D:/java-project/multi-agent-kb
git add frontend/index.html frontend/src/App.vue frontend/src/composables/useTheme.js
git commit -m "feat: design system + theme switching + page transitions"
```

---

### Task 2: 通用组件 - EmptyState + SkeletonLoader

**Files:**
- Create: `frontend/src/components/EmptyState.vue`
- Create: `frontend/src/components/SkeletonLoader.vue`

- [ ] **Step 1: 创建 EmptyState 组件**

```vue
<!-- frontend/src/components/EmptyState.vue -->
<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <div class="empty-title">{{ title }}</div>
    <div class="empty-desc">{{ description }}</div>
    <slot name="action"></slot>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '◇' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  font-size: 48px; margin-bottom: 16px;
  opacity: 0.4; line-height: 1;
}
.empty-title {
  font-family: var(--font-display);
  font-size: 16px; font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.empty-desc {
  font-size: 13px; color: var(--text-muted);
  max-width: 280px; line-height: 1.5;
}
</style>
```

- [ ] **Step 2: 创建 SkeletonLoader 组件**

```vue
<!-- frontend/src/components/SkeletonLoader.vue -->
<template>
  <div class="skeleton" :style="{ width, height, borderRadius: radius }"></div>
</template>

<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '16px' },
  radius: { type: String, default: '8px' },
})
</script>

<style scoped>
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-hover) 25%,
    var(--bg-card) 50%,
    var(--bg-hover) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

- [ ] **Step 3: 验证**

在任意页面临时引入组件确认渲染正常。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/EmptyState.vue frontend/src/components/SkeletonLoader.vue
git commit -m "feat: add EmptyState and SkeletonLoader components"
```

---

### Task 3: 文档管理页重构

**Files:**
- Modify: `frontend/src/components/DocumentManager.vue`

- [ ] **Step 1: 重写 DocumentManager.vue**

完整替换为新版本，包含：
- 统计卡片：渐变背景 + hover 浮起 + 数字用 DM Sans 粗体
- 处理流水线：竖向步骤条（编号圆圈 + 连接线 + 完成动画）
- 文档列表：卡片网格布局 + 类型图标 + 删除按钮
- 空状态：使用 EmptyState 组件

```vue
<!-- frontend/src/components/DocumentManager.vue 完整重写 -->
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
          <div class="step-line" v-if="true"></div>
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

/* 统计卡片 */
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

/* 上传区 */
.upload-area { width: 100%; }

.upload-inner {
  padding: 32px; text-align: center;
}

.upload-icon {
  font-size: 36px; color: var(--text-muted);
  margin-bottom: 8px; opacity: 0.5;
}

.upload-text {
  color: var(--text-secondary); font-size: 14px;
}
.upload-text em {
  color: var(--accent); font-style: normal;
  font-weight: 600;
}
.upload-hint {
  color: var(--text-muted); font-size: 12px;
  margin-top: 4px;
}

/* 流水线 */
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

/* 文档网格 */
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
```

- [ ] **Step 2: 验证**

1. 统计卡片 hover 有浮起效果
2. 流水线步骤条正确显示连接线和状态
3. 文档列表为卡片网格，删除按钮 hover 变红
4. 空状态显示 EmptyState 组件

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DocumentManager.vue
git commit -m "feat: redesign DocumentManager with editorial style"
```

---

### Task 4: 智能问答页重构

**Files:**
- Modify: `frontend/src/components/ChatInterface.vue`

- [ ] **Step 1: 重写 ChatInterface.vue**

```vue
<!-- frontend/src/components/ChatInterface.vue 完整重写 -->
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

/* 快捷问题 */
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

/* 对话布局 */
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

/* 消息 */
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

/* 打字动画 */
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

/* 输入框 */
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

/* Agent 时间线 */
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

.panel-empty {
  text-align: center; padding: 40px 0;
}
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

/* 检索片段 */
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
```

- [ ] **Step 2: 验证**

1. 快捷问题卡片有交错入场动画
2. 消息气泡样式正确（用户橙色渐变、AI 白底）
3. Agent 面板改为时间线样式，带彩色圆点
4. 输入框聚焦时底部有琥珀色发光线

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatInterface.vue
git commit -m "feat: redesign ChatInterface with timeline agent panel"
```

---

### Task 5: 知识图谱页重构

**Files:**
- Modify: `frontend/src/components/KnowledgeGraph.vue`

- [ ] **Step 1: 重写 KnowledgeGraph.vue**

保留图谱渲染逻辑不变，改造 UI 部分：
- 工具栏加毛玻璃效果
- 空状态使用 EmptyState 组件
- 右键菜单和撤销按钮样式适配新主题
- 节点详情浮层加进入动画

由于 KnowledgeGraph.vue 的核心逻辑（ECharts 渲染、右键删除、撤销栈）不需要改变，只改造外层 UI 壳：

修改以下部分：
1. `<style>` 中所有颜色值改为 CSS 变量
2. `.graph-toolbar` 加 `backdrop-filter: blur(12px)` + `background: var(--bg-topbar)`
3. `.empty-state` 使用 EmptyState 组件替换
4. `.context-menu` 适配新主题色
5. `.undo-bar` 样式适配

- [ ] **Step 2: 验证**

1. 工具栏有毛玻璃效果
2. 空状态显示正确
3. 右键菜单样式适配深浅色
4. 图谱正常渲染

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/KnowledgeGraph.vue
git commit -m "feat: adapt KnowledgeGraph to new design system"
```

---

### Task 6: 最终验证 + 推送

- [ ] **Step 1: 完整功能验证**

1. 浏览器打开 http://localhost:5173
2. 验证三个页面都能正常切换（有过渡动画）
3. 点击深浅色切换按钮，确认所有页面颜色正确切换
4. 折叠/展开侧边栏
5. 文档管理：上传 → 抽取 → 入库 全流程
6. 智能问答：发送问题，查看 Agent 时间线
7. 知识图谱：右键删除 → 撤销

- [ ] **Step 2: Push to GitHub**

```bash
cd D:/java-project/multi-agent-kb
git config --global --unset url.https://kkgithub.com/.insteadOf
git push
git config --global url.https://kkgithub.com/.insteadOf https://github.com/
```
