# 前端界面重构设计文档

> **目标：** 将 multi-agent-kb 前端从"学生作业"级别升级为高端商务风格（Vercel/Linear 级别），支持深浅色切换、页面动效、响应式布局、完善交互状态。

**技术方案：** 渐进式重构，保留 Vue3 + Element Plus 架构，用 CSS 变量 + Vue Transition 改造，不引入新依赖。

---

## 1. 设计系统（CSS 变量）

### 1.1 颜色系统

通过 `data-theme` 属性切换主题，所有颜色通过 CSS 变量引用。

**亮色主题：**
```
--bg-page: #fafafa
--bg-card: #ffffff
--bg-hover: #f5f7fa
--bg-active: #f0f5ff
--text-primary: #1a1a2e
--text-secondary: #6b7280
--text-muted: #9ca3af
--border: #e5e7eb
--border-light: #f3f4f6
--accent: #2563eb
--accent-hover: #1d4ed8
--accent-soft: #dbeafe
--success: #10b981
--warning: #f59e0b
--danger: #ef4444
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--shadow-md: 0 4px 12px rgba(0,0,0,0.08)
--shadow-lg: 0 8px 24px rgba(0,0,0,0.12)
```

**暗色主题：**
```
--bg-page: #0f0f1a
--bg-card: #1a1a2e
--bg-hover: #252540
--bg-active: #1e3a5f
--text-primary: #e5e7eb
--text-secondary: #9ca3af
--text-muted: #6b7280
--border: #2d2d44
--border-light: #1f1f35
--accent: #3b82f6
--accent-hover: #60a5fa
--accent-soft: #1e3a5f
--success: #34d399
--warning: #fbbf24
--danger: #f87171
--shadow-sm: 0 1px 2px rgba(0,0,0,0.2)
--shadow-md: 0 4px 12px rgba(0,0,0,0.3)
--shadow-lg: 0 8px 24px rgba(0,0,0,0.4)
```

### 1.2 间距和圆角

```
--radius-sm: 6px
--radius-md: 10px
--radius-lg: 14px
--radius-xl: 20px
--gap-xs: 4px
--gap-sm: 8px
--gap-md: 16px
--gap-lg: 24px
--gap-xl: 32px
```

### 1.3 实现方式

在 `App.vue` 的 `<style>` 中定义 `:root` 和 `[data-theme="dark"]` 两套变量。JS 通过 `document.documentElement.dataset.theme` 切换。

---

## 2. 侧边栏重构

### 2.1 亮色模式
- 背景：纯白 `#ffffff`
- 选中项：左侧 3px 蓝色指示条 + `--bg-active` 背景
- hover：`--bg-hover` 背景过渡（200ms）

### 2.2 暗色模式
- 背景：`#12121f`（比主背景深一级）
- logo 区域：微妙渐变底色 + 发光效果（`box-shadow: 0 0 20px rgba(59,130,246,0.15)`）
- 选中项：左侧蓝色指示条 + 半透明蓝色背景

### 2.3 折叠状态
- 宽度从 200px 缩为 64px
- 只显示图标，文字隐藏
- 顶栏加一个展开/折叠按钮（`<<` / `>>`）
- 过渡动画 300ms ease

### 2.4 响应式
- `< 768px`：侧边栏隐藏，底部出现 Tab 栏（固定定位）
- `768px - 1024px`：侧边栏默认折叠（64px）
- `> 1024px`：侧边栏默认展开（200px）

---

## 3. 顶栏重构

### 3.1 布局
- 左侧：页面标题
- 右侧：技术栈标签 + 深浅色切换按钮 + 侧边栏折叠按钮

### 3.2 深浅色切换
- 太阳/月亮 SVG 图标
- 点击切换 `data-theme` 属性
- 状态持久化到 `localStorage`
- 切换时 300ms 过渡（所有颜色平滑过渡）

### 3.3 技术栈标签
- 改为更精致的胶囊样式（pill shape）
- 暗色模式下颜色适配

---

## 4. 页面切换动效

### 4.1 Vue Transition

三个页面组件用 `<Transition>` 包裹：

```vue
<Transition name="page" mode="out-in">
  <DocumentManager v-if="activeTab === 'docs'" />
  <ChatInterface v-else-if="activeTab === 'chat'" />
  <KnowledgeGraph v-else-if="activeTab === 'graph'" />
</Transition>
```

CSS 动画：
```css
.page-enter-active, .page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
```

### 4.2 侧边栏选中指示条

```css
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
  transition: height 0.2s ease;
}
```

---

## 5. 交互状态补齐

### 5.1 骨架屏

为三个页面各设计一套骨架屏组件：

**文档管理页骨架：**
- 统计卡片区域：4 个灰色矩形占位
- 上传区域：灰色虚线框占位
- 文档列表：3 行灰色条纹占位

**智能问答页骨架：**
- 快捷问题区域：4 个灰色卡片占位
- 对话区域：2-3 个灰色气泡占位

**知识图谱页骨架：**
- 工具栏：灰色条纹占位
- 图谱区域：中央灰色圆形 + 辐射线条占位

### 5.2 空状态

每个页面有专属空状态：

**文档管理：** 上传图标 + "暂无文档，上传文件开始使用"
**智能问答：** 对话图标 + "输入问题开始探索知识库"
**知识图谱：** 图谱图标 + "暂无图谱数据，请先上传文档并执行实体抽取"

### 5.3 错误状态

- 网络请求失败：Toast 提示 + 重试按钮
- 后端未启动：顶栏状态标签变为红色 + 提示文字

### 5.4 操作反馈

- 按钮点击：loading 状态 + 禁用
- 成功操作：绿色 Toast（自动消失 3s）
- 失败操作：红色 Toast（自动消失 5s）
- 删除操作：确认弹窗 + 撤销机会

---

## 6. 三个页面的具体改造

### 6.1 文档管理页

**统计卡片：**
- 加微妙渐变背景（从白到淡蓝）
- hover 时轻微上浮（`transform: translateY(-2px)`）+ 阴影加深
- 数字用大号字体 + 主色

**处理流水线：**
- 改为竖向步骤条样式
- 每步有编号圆圈 + 连接线
- 已完成步骤：绿色圆圈 + 绿色连接线
- 当前步骤：蓝色圆圈 + 脉冲动画
- 未完成步骤：灰色圆圈

**文档列表：**
- 改为卡片网格（每行 2-3 个）
- 每张卡片：文件类型图标 + 文件名 + 大小/切片数 + 删除按钮
- hover 时边框变色 + 阴影

### 6.2 智能问答页

**快捷问题：**
- 卡片加渐变边框（透明到蓝色）hover 效果
- 图标从 `→` 改为更精致的 SVG 图标

**消息气泡：**
- 用户消息：蓝色渐变背景 + 白色文字 + 右对齐
- AI 消息：`--bg-card` 背景 + 微妙阴影 + 左对齐
- 头像：渐变背景 + 白色首字母

**Agent 协同面板：**
- 改为竖向时间线样式
- 每个 Agent 节点：左侧彩色圆点 + 连接线 + 卡片
- 已完成：绿色圆点 + 打勾动画
- 进行中：蓝色圆点 + 脉冲动画
- 检索片段：卡片样式，带序号和高亮关键词

**输入框：**
- 聚焦时底部出现蓝色发光线条（`box-shadow: 0 2px 0 var(--accent)`）
- 发送按钮改为渐变蓝色
- placeholder 用 `--text-muted` 颜色

### 6.3 知识图谱页

**工具栏：**
- 加毛玻璃效果（`backdrop-filter: blur(10px)`）
- 按钮改为更精致的样式

**图谱容器：**
- 背景改为更微妙的渐变
- 暗色模式下渐变色调偏深蓝

**空状态：**
- 居中大图标 + 标题 + 引导文案

**节点详情浮层：**
- 加进入动画（缩放 + 淡入）
- 头像用渐变背景 + 发光效果

---

## 7. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/App.vue` | 重构 | CSS 变量定义、布局改造、主题切换、Transition、响应式 |
| `frontend/src/components/DocumentManager.vue` | 重构 | 统计卡片、流水线、文档列表卡片化、骨架屏、空状态 |
| `frontend/src/components/ChatInterface.vue` | 重构 | 消息气泡、Agent 面板时间线、输入框、骨架屏 |
| `frontend/src/components/KnowledgeGraph.vue` | 重构 | 工具栏毛玻璃、空状态、浮层动画 |
| `frontend/src/composables/useTheme.js` | 新建 | 主题切换逻辑（localStorage 持久化） |
| `frontend/src/components/SkeletonLoader.vue` | 新建 | 通用骨架屏组件 |
| `frontend/src/components/EmptyState.vue` | 新建 | 通用空状态组件 |

---

## 8. 不做的事（YAGNI）

- 不引入 Tailwind CSS 或其他 CSS 框架
- 不引入新的组件库（保留 Element Plus）
- 不做 SSR 或 SSG
- 不做国际化
- 不做自定义字体（用系统字体栈）
- 不做复杂的图表动画（ECharts 本身够用）
