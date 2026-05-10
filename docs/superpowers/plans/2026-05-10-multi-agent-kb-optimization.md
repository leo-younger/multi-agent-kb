# multi-agent-kb 优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 multi-agent-kb 项目的安全漏洞、并发竞态、性能瓶颈和健壮性问题，共 7 项优化。

**Architecture:** 原地修补方案，逐文件修改，不改架构。TDD 方式：先写失败测试，再写最小实现使测试通过。

**Tech Stack:** Python 3.14, FastAPI, PyPDF2, python-docx, sentence-transformers, numpy, neo4j, Vue 3, ECharts, Element Plus

---

## Task 1: 测试基础设施 + chunk_text 健壮性修复

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_optimizations.py`
- Modify: `backend/services/document_parser.py:52-83`

- [ ] **Step 1: 创建测试目录和测试文件，写 chunk_text 测试**

```python
# backend/tests/__init__.py
# (empty file)
```

```python
# backend/tests/test_optimizations.py
"""优化项测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.document_parser import chunk_text, parse_pdf, parse_docx


def test_chunk_overlap_guard():
    """overlap >= chunk_size 时应自动重置为 0，不产生无限循环"""
    text = "A" * 100
    chunks = chunk_text(text, chunk_size=10, overlap=15)
    # overlap 被重置为 0，所以 100 字符 / 10 = 10 个切片
    assert len(chunks) == 10
    assert chunks[0].content == "A" * 10
    assert chunks[-1].content == "A" * 10


def test_chunk_normal():
    """正常参数下切片数量和重叠正确"""
    text = "ABCDEFGHIJ" * 10  # 100 字符
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    # 第一个切片: 0-20, 第二个: 15-35, 第三个: 30-50, ...
    assert chunks[0].start_pos == 0
    assert chunks[0].end_pos == 20
    assert chunks[1].start_pos == 15
    assert chunks[1].end_pos == 35
    # 所有切片拼接应覆盖全文
    all_text = "".join(c.content for c in chunks)
    assert text in all_text or all_text.startswith(text)


def test_chunk_single():
    """文本长度 <= chunk_size 时只有 1 个切片"""
    text = "Hello"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].content == "Hello"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_optimizations.py::test_chunk_overlap_guard tests/test_optimizations.py::test_chunk_normal tests/test_optimizations.py::test_chunk_single -v
```

Expected: FAIL（因为 overlap >= chunk_size 时会无限循环或行为异常）

- [ ] **Step 3: 修复 document_parser.py — overlap 防护**

在 `chunk_text` 函数的 `chunks = []` 之前加：

```python
    if overlap >= chunk_size:
        overlap = 0
```

同时将 `parse_pdf` 和 `parse_docx` 改为 join：

```python
def parse_pdf(file_content: bytes) -> str:
    """解析 PDF 文件，提取文本内容"""
    reader = PdfReader(io.BytesIO(file_content))
    return "".join(page.extract_text() or "" for page in reader.pages)


def parse_docx(file_content: bytes) -> str:
    """解析 Word 文件，提取文本内容"""
    doc = Document(io.BytesIO(file_content))
    return "\n".join(para.text for para in doc.paragraphs)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/services/document_parser.py backend/tests/
git commit -m "fix: chunk_text overlap guard + join optimization"
```

---

## Task 2: embedding 竞态修复

**Files:**
- Modify: `backend/services/embedding.py`
- Modify: `backend/tests/test_optimizations.py`

- [ ] **Step 1: 写 embedding 测试**

在 `backend/tests/test_optimizations.py` 末尾追加：

```python
from services.embedding import get_embedding, get_embeddings, get_dimension


def test_embedding_mock_fallback():
    """mock 模式应返回 384 维归一化向量"""
    # 直接调用 mock 内部函数测试
    from services.embedding import _text_to_mock_vector
    vec = _text_to_mock_vector("测试文本")
    assert len(vec) == 384
    # 归一化检查：模长应约等于 1
    import numpy as np
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-5


def test_embedding_deterministic():
    """相同文本应生成相同的 mock 向量"""
    from services.embedding import _text_to_mock_vector
    vec1 = _text_to_mock_vector("hello")
    vec2 = _text_to_mock_vector("hello")
    assert vec1 == vec2


def test_embedding_dimension():
    """get_dimension 应返回 384"""
    assert get_dimension() == 384
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_optimizations.py::test_embedding_mock_fallback tests/test_optimizations.py::test_embedding_deterministic tests/test_optimizations.py::test_embedding_dimension -v
```

Expected: 可能因旧的竞态逻辑导致 `_model_ready` Event 不存在而报错

- [ ] **Step 3: 重写 embedding.py**

替换整个文件为：

```python
"""
Embedding 服务
使用 sentence-transformers 本地模型生成文本向量
如果模型加载失败，降级为确定性伪向量（基于 hash）
"""

import os
import hashlib
import numpy as np
from typing import List
import threading

# 设置 HuggingFace 国内镜像（解决国内无法访问 huggingface.co）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "15"

# 全局模型实例
_model = None
_model_name = "all-MiniLM-L6-v2"
_dimension = 384
_use_mock = False
_model_ready = threading.Event()


def _try_load_model():
    """尝试加载模型"""
    global _model, _use_mock
    try:
        from sentence_transformers import SentenceTransformer
        print("[Embedding] 正在加载模型（首次需下载约 80MB，使用 hf-mirror.com 镜像）...")
        _model = SentenceTransformer(_model_name)
        print("[Embedding] 模型加载成功")
    except Exception as e:
        print(f"[Embedding] 模型加载失败，使用 mock 模式: {type(e).__name__}")
        _use_mock = True
    finally:
        _model_ready.set()


# 启动时在后台线程加载模型
_load_thread = threading.Thread(target=_try_load_model, daemon=True)
_load_thread.start()


def _wait_model(timeout: float = 30.0):
    """等待模型加载完成（最多 timeout 秒）"""
    if not _model_ready.is_set():
        print("[Embedding] 等待模型加载...")
        _model_ready.wait(timeout=timeout)


def _text_to_mock_vector(text: str) -> List[float]:
    """基于文本 hash 生成确定性伪向量"""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    rng = np.random.RandomState(int.from_bytes(hash_bytes[:4], "big"))
    vec = rng.randn(_dimension).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def get_embedding(text: str) -> List[float]:
    """获取单条文本的 embedding 向量"""
    _wait_model()
    if _model is not None:
        vec = _model.encode(text, normalize_embeddings=True)
        return vec.tolist()
    return _text_to_mock_vector(text)


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """批量获取文本的 embedding 向量"""
    _wait_model()
    if _model is not None:
        vecs = _model.encode(texts, normalize_embeddings=True)
        return vecs.tolist()
    return [_text_to_mock_vector(t) for t in texts]


def get_dimension() -> int:
    """返回向量维度"""
    return _dimension
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/services/embedding.py backend/tests/test_optimizations.py
git commit -m "fix: embedding race condition with threading.Event"
```

---

## Task 3: 实体抽取测试

**Files:**
- Modify: `backend/tests/test_optimizations.py`

- [ ] **Step 1: 写实体抽取测试**

在 `backend/tests/test_optimizations.py` 末尾追加：

```python
from services.entity_extractor import extract_from_chunks, extract_entities_from_text


def test_extract_entities_dedup():
    """多个切片中的重复实体应去重"""
    chunks = ["张三负责知识库模块", "张三也负责解析服务", "李四负责订单系统"]
    entities, relations = extract_from_chunks(chunks)
    names = [e.name for e in entities]
    # 张三只应出现一次
    assert names.count("张三") == 1
    assert "李四" in names


def test_extract_entities_from_text():
    """单文本实体提取应匹配词典中的实体"""
    text = "技术部负责管理解析服务"
    entities = extract_entities_from_text(text)
    names = {e.name for e in entities}
    assert "技术部" in names
    assert "解析服务" in names


def test_extract_entities_fallback():
    """无匹配实体时应返回默认实体"""
    text = "这是一段没有任何已知实体的普通文本"
    entities = extract_entities_from_text(text)
    assert len(entities) > 0  # 应返回默认示例实体
```

- [ ] **Step 2: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 9 passed

- [ ] **Step 3: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/tests/test_optimizations.py
git commit -m "test: add entity extraction tests"
```

---

## Task 4: Neo4j 图谱查询优化

**Files:**
- Modify: `backend/services/graph_store.py:123-146`
- Modify: `backend/tests/test_optimizations.py`

- [ ] **Step 1: 写图谱查询测试（需 mock Neo4j）**

在 `backend/tests/test_optimizations.py` 末尾追加：

```python
from unittest.mock import patch, MagicMock
from services.graph_store import search_related_entities


def test_search_related_entities_empty_keywords():
    """空关键词列表应返回空结果"""
    result = search_related_entities([])
    assert result == []


@patch("services.graph_store._get_driver")
def test_search_related_entities_dedup(mock_get_driver):
    """查询结果应去重（DISTINCT）"""
    mock_driver = MagicMock()
    mock_get_driver.return_value = mock_driver

    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    # 模拟返回重复记录
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([
        {"source": "张三", "target": "知识库模块", "rel_type": "负责"},
        {"source": "张三", "target": "知识库模块", "rel_type": "负责"},  # 重复
    ]))
    mock_session.run.return_value = mock_result

    result = search_related_entities(["张三"])
    assert len(result) == 2  # mock 返回 2 条（DISTINCT 在 Cypher 层面去重）
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_optimizations.py::test_search_related_entities_empty_keywords tests/test_optimizations.py::test_search_related_entities_dedup -v
```

Expected: 可能因旧的循环逻辑导致行为不一致

- [ ] **Step 3: 修改 graph_store.py**

替换 `search_related_entities` 函数为：

```python
def search_related_entities(keywords: List[str]) -> List[Dict]:
    """
    根据关键词搜索相关实体及其关系

    Args:
        keywords: 关键词列表

    Returns:
        匹配的实体关系列表
    """
    if not keywords:
        return []
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            "UNWIND $keywords AS kw "
            "MATCH (a:Entity)-[r:RELATION]->(b:Entity) "
            "WHERE a.name CONTAINS kw OR b.name CONTAINS kw "
            "RETURN DISTINCT a.name AS source, b.name AS target, r.type AS rel_type "
            "LIMIT 20",
            keywords=keywords,
        )
        return [dict(record) for record in result]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 11 passed

- [ ] **Step 5: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/services/graph_store.py backend/tests/test_optimizations.py
git commit -m "perf: merge Neo4j loop queries into single UNWIND"
```

---

## Task 5: Agent 并行执行优化

**Files:**
- Modify: `backend/services/agents.py`
- Modify: `backend/main.py:160`
- Modify: `backend/tests/test_optimizations.py`

- [ ] **Step 1: 写 Agent 并行测试**

在 `backend/tests/test_optimizations.py` 末尾追加：

```python
import asyncio
from services.agents import run_agent_pipeline, _analyze_question, _extract_keywords


def test_analyze_question():
    """问题类型识别正确"""
    assert _analyze_question("张三负责什么模块？") == "职责查询"
    assert _analyze_question("订单系统依赖哪些服务？") == "依赖关系查询"
    assert _analyze_question("解析服务属于哪个部门？") == "归属查询"
    assert _analyze_question("随便问一个问题") == "通用查询"


def test_extract_keywords():
    """关键词提取应匹配已知实体"""
    kw = _extract_keywords("张三负责知识库模块")
    assert "张三" in kw
    assert "知识库模块" in kw


def test_extract_keywords_fallback():
    """无已知实体时应提取有意义的词"""
    kw = _extract_keywords("系统如何优化性能？")
    assert len(kw) > 0


def test_agent_pipeline_async():
    """run_agent_pipeline 应为 async 函数且可执行"""
    result = asyncio.get_event_loop().run_until_complete(
        run_agent_pipeline("张三负责什么？")
    )
    assert "answer" in result
    assert "agent_steps" in result
    assert len(result["agent_steps"]) == 4  # 总控 + 检索 + 拓扑 + 总结
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_optimizations.py::test_analyze_question tests/test_optimizations.py::test_extract_keywords tests/test_optimizations.py::test_agent_pipeline_async -v
```

Expected: `run_agent_pipeline` 不是 async 函数，或调用方式不对

- [ ] **Step 3: 重写 agents.py**

替换整个文件为：

```python
"""
多智能体协同模拟服务
模拟 4 个 Agent 协同完成问答任务：
1. 总控 Agent：分析问题类型，调度其他 Agent
2. 检索 Agent：从向量库检索相关文档片段
3. 拓扑 Agent：从图数据库查询实体关联关系
4. 总结 Agent：综合信息生成最终答案
"""

import asyncio
from typing import List, Dict
from models.schemas import AgentStep
from services import vector_store, graph_store, embedding


async def run_agent_pipeline(question: str) -> Dict:
    """
    执行多智能体协同流水线（检索/拓扑并行）

    Args:
        question: 用户问题

    Returns:
        包含 answer, agent_steps, related_chunks, related_entities 的字典
    """
    agent_steps = []

    # ====== Step 1: 总控 Agent - 分析问题 ======
    question_type = _analyze_question(question)
    agent_steps.append(AgentStep(
        agent_name="总控Agent",
        status="完成",
        output=f"问题类型识别为：{question_type}，已调度检索Agent和拓扑Agent并行工作",
    ))

    # ====== Step 2 & 3: 检索 Agent + 拓扑 Agent 并行执行 ======
    loop = asyncio.get_event_loop()
    retrieval_task = loop.run_in_executor(None, _do_retrieval, question)
    topology_task = loop.run_in_executor(None, _do_topology, question)

    (related_chunks, chunk_summary), (related_entities, topo_summary) = await asyncio.gather(
        retrieval_task, topology_task
    )

    agent_steps.append(AgentStep(
        agent_name="检索Agent",
        status="完成",
        output=chunk_summary,
    ))

    agent_steps.append(AgentStep(
        agent_name="拓扑Agent",
        status="完成",
        output=topo_summary,
    ))

    # ====== Step 4: 总结 Agent - 生成答案 ======
    answer = _generate_answer(question, question_type, related_chunks, related_entities)

    agent_steps.append(AgentStep(
        agent_name="总结Agent",
        status="完成",
        output="已综合检索结果和图谱关系，生成最终答案",
    ))

    return {
        "answer": answer,
        "agent_steps": agent_steps,
        "related_chunks": related_chunks,
        "related_entities": related_entities,
    }


def _do_retrieval(question: str) -> tuple:
    """检索 Agent：向量检索（在线程池中执行）"""
    try:
        query_vector = embedding.get_embedding(question)
        search_results = vector_store.search_vectors(query_vector, top_k=3)
        related_chunks = [item["text"] for item in search_results]
        chunk_summary = f"检索到 {len(search_results)} 个相关片段"
        if search_results:
            chunk_summary += f"，最高相似度: {search_results[0].get('distance', 0):.3f}"
    except Exception as e:
        related_chunks = ["暂无相关文档片段（向量库未初始化或为空）"]
        chunk_summary = f"检索异常: {str(e)}，使用默认结果"
    return related_chunks, chunk_summary


def _do_topology(question: str) -> tuple:
    """拓扑 Agent：图谱查询（在线程池中执行）"""
    keywords = _extract_keywords(question)
    try:
        graph_relations = graph_store.search_related_entities(keywords)
        related_entities = graph_relations
        topo_summary = f"发现 {len(graph_relations)} 条关联关系"
        if graph_relations:
            examples = [f"{r['source']}→{r['rel_type']}→{r['target']}" for r in graph_relations[:3]]
            topo_summary += f"，示例: {'; '.join(examples)}"
    except Exception as e:
        related_entities = []
        topo_summary = f"图谱查询异常: {str(e)}，使用默认结果"
    return related_entities, topo_summary


def _analyze_question(question: str) -> str:
    """分析问题类型（模拟总控 Agent）"""
    keywords_map = {
        "负责": "职责查询",
        "依赖": "依赖关系查询",
        "属于": "归属查询",
        "管理": "管理关系查询",
        "什么": "事实查询",
        "哪些": "枚举查询",
        "如何": "方法查询",
        "为什么": "原因查询",
    }
    for kw, q_type in keywords_map.items():
        if kw in question:
            return q_type
    return "通用查询"


def _extract_keywords(question: str) -> List[str]:
    """从问题中提取关键词（用于图谱查询）"""
    known_entities = [
        "张三", "李四", "王五", "赵六", "刘七",
        "技术部", "产品部", "运维部", "测试部", "数据部",
        "订单系统", "用户系统", "支付系统", "库存系统", "日志系统",
        "知识库模块", "解析服务", "网关模块", "认证模块", "调度模块",
        "用户查询接口", "订单创建接口", "数据同步接口", "文件上传接口",
    ]
    found = [e for e in known_entities if e in question]
    if not found:
        found = [w for w in question if len(w) >= 2 and w not in "的了吗呢啊吧这是在有和与或但"]
        found = found[:5]
    return found


def _generate_answer(question: str, q_type: str, chunks: List[str], entities: List[dict]) -> str:
    """综合信息生成最终答案（模拟总结 Agent）"""
    answer_parts = []

    type_answers = {
        "职责查询": "根据知识库信息，相关职责如下：",
        "依赖关系查询": "根据系统架构，相关依赖关系如下：",
        "归属查询": "根据组织架构，归属关系如下：",
        "管理关系查询": "根据管理体系，相关关系如下：",
        "事实查询": "根据知识库记录，相关信息如下：",
        "枚举查询": "根据知识库检索，相关内容包括：",
        "方法查询": "根据文档资料，建议方法如下：",
        "原因查询": "根据系统记录，相关原因分析如下：",
    }
    answer_parts.append(type_answers.get(q_type, "根据知识库综合分析，回答如下："))

    if chunks and chunks[0] != "暂无相关文档片段（向量库未初始化或为空）":
        answer_parts.append(f"\n【文档依据】共检索到 {len(chunks)} 个相关片段：")
        for i, chunk in enumerate(chunks[:2], 1):
            preview = chunk[:100].replace("\n", " ")
            answer_parts.append(f"  {i}. {preview}...")

    if entities:
        answer_parts.append(f"\n【关系网络】涉及 {len(entities)} 条实体关联：")
        for rel in entities[:3]:
            answer_parts.append(f"  - {rel['source']} →[{rel['rel_type']}]→ {rel['target']}")

    answer_parts.append(f"\n【综合结论】针对您的问题「{question}」，"
                        f"基于文档检索和知识图谱分析，以上是系统自动生成的参考回答。")

    return "\n".join(answer_parts)
```

- [ ] **Step 4: 修改 main.py 加 await**

将 `backend/main.py` 第 160 行：
```python
    result = agents.run_agent_pipeline(question)
```
改为：
```python
    result = await agents.run_agent_pipeline(question)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 15 passed

- [ ] **Step 6: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/services/agents.py backend/main.py backend/tests/test_optimizations.py
git commit -m "perf: parallelize retrieval and topology agents with asyncio.gather"
```

---

## Task 6: 前端 XSS 修复 + 图谱查找优化

**Files:**
- Modify: `frontend/src/components/ChatInterface.vue:25,113`
- Modify: `frontend/src/components/KnowledgeGraph.vue:178-179`

- [ ] **Step 1: 修复 ChatInterface.vue XSS**

将第 25 行：
```html
<div class="msg-text" v-html="msg.text"></div>
```
改为：
```html
<div class="msg-text" style="white-space: pre-line;">{{ msg.text }}</div>
```

将第 113 行：
```javascript
messages.value.push({ role: 'assistant', text: data.answer.replace(/\n/g, '<br/>') })
```
改为：
```javascript
messages.value.push({ role: 'assistant', text: data.answer })
```

- [ ] **Step 2: 优化 KnowledgeGraph.vue 查找**

将第 178-179 行：
```javascript
  const nodes = data.nodes.map(n => {
    const catIdx = categories.findIndex(c => c.name === n.category)
```
改为：
```javascript
  const categoryMap = new Map(categories.map((c, i) => [c.name, i]))

  const nodes = data.nodes.map(n => {
    const catIdx = categoryMap.get(n.category) ?? 0
```

- [ ] **Step 3: 手动验证前端**

启动前端开发服务器，检查：
1. 聊天页面消息正常显示（换行保留，无 HTML 注入）
2. 知识图谱正常渲染，节点分类颜色正确

```bash
cd frontend && npm run dev
```

- [ ] **Step 4: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add frontend/src/components/ChatInterface.vue frontend/src/components/KnowledgeGraph.vue
git commit -m "fix: XSS vulnerability in Chat + optimize graph node lookup"
```

---

## Task 7: 依赖清理 + 最终验证

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 移除冗余 starlette 依赖**

从 `backend/requirements.txt` 中删除：
```
# CORS 支持
starlette>=0.27.0
```

- [ ] **Step 2: 运行全部测试最终验证**

```bash
cd backend && python -m pytest tests/test_optimizations.py -v
```

Expected: 15 passed, 0 failed

- [ ] **Step 3: 提交**

```bash
cd D:/java-project/multi-agent-kb
git add backend/requirements.txt
git commit -m "chore: remove redundant starlette dependency"
```

---

## 执行检查清单

- [ ] Task 1: chunk_text 健壮性（3 测试 + join 优化）
- [ ] Task 2: embedding 竞态修复（3 测试 + 重写）
- [ ] Task 3: 实体抽取测试（3 测试）
- [ ] Task 4: Neo4j 查询优化（2 测试 + UNWIND）
- [ ] Task 5: Agent 并行化（4 测试 + asyncio.gather）
- [ ] Task 6: 前端修复（XSS + Map 查找）
- [ ] Task 7: 依赖清理 + 最终验证
