# multi-agent-kb 优化设计文档

日期：2026-05-10
方案：A — 原地修补（不改架构，逐文件修改）

## 背景

multi-agent-kb 是一个多智能体协同知识库 MVP 系统（Python FastAPI + Vue3），代码审查发现以下问题：

- **安全**：XSS 漏洞（`v-html` 渲染未过滤内容）
- **并发**：embedding 模型加载竞态（首次调用可能降级为 mock 不自知）
- **健壮性**：`chunk_text` 缺少参数防护
- **性能**：字符串拼接、循环查询、串行执行、线性查找
- **维护**：冗余依赖

## 改动清单

### 1. 安全修复 — ChatInterface.vue

**文件**：`frontend/src/components/ChatInterface.vue`

| 改动点 | 改动内容 |
|--------|---------|
| 第 25 行 | `v-html="msg.text"` → `{{ msg.text }}` + `white-space: pre-line` |
| 第 113 行 | 移除 `.replace(/\n/g, '<br/>')`，纯文本直接存储 |

### 2. 并发修复 — embedding.py

**文件**：`backend/services/embedding.py`

重写模型加载逻辑：
- 用 `threading.Event` 作为就绪信号（替代 `_load_started` 布尔标志 + `_load_lock`）
- 启动时即创建后台加载线程（不再延迟到首次调用）
- `get_embedding()` / `get_embeddings()` 首次调用时 `_model_ready.wait(timeout=30)` 阻塞等待
- 加载完成后（成功或失败）`_model_ready.set()`，后续调用零开销
- 保持 mock 降级策略

### 3. 健壮性修复 — document_parser.py

**文件**：`backend/services/document_parser.py`

| 改动点 | 改动内容 |
|--------|---------|
| `chunk_text` 入口 | 加 `if overlap >= chunk_size: overlap = 0` 防护 |
| `parse_pdf` | `+=` 循环 → `"".join(page.extract_text() or "" for page in reader.pages)` |
| `parse_docx` | `+=` 循环 → `"\n".join(para.text for para in doc.paragraphs)` |

### 4. 性能优化 — graph_store.py

**文件**：`backend/services/graph_store.py`

`search_related_entities`：循环 N 次查询 → 单条 `UNWIND` Cypher + `DISTINCT`

```cypher
UNWIND $keywords AS kw
MATCH (a:Entity)-[r:RELATION]->(b:Entity)
WHERE a.name CONTAINS kw OR b.name CONTAINS kw
RETURN DISTINCT a.name AS source, b.name AS target, r.type AS rel_type
LIMIT 20
```

### 5. 性能优化 — agents.py + main.py

**文件**：`backend/services/agents.py`、`backend/main.py`

- `run_agent_pipeline` 改为 `async def`
- 检索 Agent 和拓扑 Agent 用 `asyncio.gather` + `loop.run_in_executor` 并行执行
- `main.py` 中调用加 `await`

### 6. 性能优化 — KnowledgeGraph.vue

**文件**：`frontend/src/components/KnowledgeGraph.vue`

- 节点分类查找：`categories.findIndex()` → 预构建 `Map<category, index>`

### 7. 维护清理 — requirements.txt

**文件**：`backend/requirements.txt`

- 移除冗余的 `starlette>=0.27.0`（FastAPI 已依赖）

## 测试计划

**文件**：`backend/tests/test_optimizations.py`（新建）

| 测试用例 | 验证内容 |
|---------|---------|
| `test_chunk_overlap_guard` | `overlap >= chunk_size` 时自动重置为 0，切片正常 |
| `test_chunk_normal` | 正常参数下切片数量和内容正确 |
| `test_parse_pdf_join` | PDF 解析返回完整拼接字符串 |
| `test_embedding_mock_fallback` | mock 模式返回 384 维归一化向量 |
| `test_embedding_wait` | 首次调用阻塞等待模型就绪 |
| `test_extract_entities` | 实体抽取去重正确 |
| `test_search_related_entities` | 图谱查询去重 |

## 不改动的部分

- 全局状态（`_uploaded_docs`、`_parsed_chunks`）— MVP 阶段够用，不在此次范围
- 实体抽取逻辑（仍为规则匹配 + mock）— 不在优化范围
- Docker / Neo4j 配置 — 不在优化范围

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| `asyncio.gather` 改变错误传播方式 | 一个 Agent 失败可能影响另一个 | 每个 Agent 内部已有 try/except 兜底 |
| embedding 等待超时 30 秒 | 首次请求可能较慢 | 后台线程启动时就开始加载，30 秒是上限 |
| Neo4j UNWIND 语法兼容性 | 旧版 Neo4j 可能不支持 | 项目使用 Neo4j 5.12，原生支持 UNWIND |
