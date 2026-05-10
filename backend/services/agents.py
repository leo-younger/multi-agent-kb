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
        import re
        found = re.findall(r'[一-鿿]{2,}', question)
        if not found:
            found = [w for w in question if len(w) >= 2 and w not in "的了吗呢啊吧这是在有和与或但？！。，"]
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
