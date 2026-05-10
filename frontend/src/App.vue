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
