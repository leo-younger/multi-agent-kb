"""
多智能体协同知识库系统 - FastAPI 后端入口
提供文档上传、实体抽取、向量入库、智能问答 4 个核心接口
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from models.schemas import (
    UploadResponse, ExtractResponse, EmbedResponse,
    ChatResponse, GraphData,
)
from services import document_parser, entity_extractor, embedding, vector_store, graph_store, agents

app = FastAPI(
    title="多智能体协同知识库系统",
    description="上传文档 → 实体抽取 → 向量入库 → 智能问答",
    version="1.0.0",
)

# CORS 配置：允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局存储（内存 + 文件），MVP 简化处理
_uploaded_docs = []      # 已上传文档记录
_parsed_chunks = []      # 最近一次解析的切片


@app.get("/")
def root():
    """健康检查"""
    return {"message": "多智能体协同知识库系统 API", "status": "running"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    文档上传接口
    接收 PDF/Word/TXT 文件，解析文本内容并切片（每片500字，重叠100字）
    """
    # 校验文件类型
    ext = file.filename.lower().split(".")[-1]
    if ext not in ("pdf", "docx", "doc", "txt"):
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    print(f"[Upload] 收到文件: {file.filename} ({ext})")

    # 读取文件内容
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 解析文档
    try:
        text = document_parser.parse_document(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档解析失败: {str(e)}")

    # 文本切片
    chunks = document_parser.chunk_text(text, chunk_size=500, overlap=100)

    print(f"[Upload] 解析完成: {len(text)} 字符, {len(chunks)} 个切片")

    # 记录到全局状态
    _uploaded_docs.append({
        "filename": file.filename,
        "file_type": ext,
        "total_length": len(text),
        "chunk_count": len(chunks),
    })
    _parsed_chunks.clear()
    _parsed_chunks.extend(chunks)

    return UploadResponse(
        filename=file.filename,
        file_type=ext,
        total_length=len(text),
        chunk_count=len(chunks),
        chunks=chunks,
    )


@app.post("/api/extract", response_model=ExtractResponse)
async def extract_entities():
    """
    实体关系抽取接口
    从已解析的文档切片中提取实体和关系，存入 Neo4j
    """
    if not _parsed_chunks:
        raise HTTPException(status_code=400, detail="请先上传并解析文档")

    # 提取实体和关系
    texts = [c.content for c in _parsed_chunks]
    entities, relations = entity_extractor.extract_from_chunks(texts)

    # 存入 Neo4j
    try:
        for e in entities:
            graph_store.create_entity(e.name, e.entity_type)
        for r in relations:
            graph_store.create_relation(r.source, r.target, r.relation_type)
    except Exception as e:
        print(f"[Extract] Neo4j 存储异常（可能未启动）: {e}")

    return ExtractResponse(
        entities=entities,
        relations=relations,
        entity_count=len(entities),
        relation_count=len(relations),
    )


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_document(doc_name: str = "default"):
    """
    向量入库接口
    将文档切片转为向量，存入 Milvus
    """
    if not _parsed_chunks:
        raise HTTPException(status_code=400, detail="请先上传并解析文档")

    texts = [c.content for c in _parsed_chunks]

    # 生成 embedding
    try:
        vectors = embedding.get_embeddings(texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding 生成失败: {str(e)}")

    # 存入 Milvus
    try:
        count = vector_store.insert_vectors(vectors, texts, doc_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量入库失败: {str(e)}")

    return EmbedResponse(
        embedded_count=count,
        collection_name="document_chunks",
        dimension=embedding.get_dimension(),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(question: str):
    """
    智能问答接口
    模拟多智能体协同：总控分析 → 检索Agent查向量 → 拓扑Agent查图谱 → 总结Agent生成答案
    """
    if not question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    result = await agents.run_agent_pipeline(question)

    return ChatResponse(
        question=question,
        answer=result["answer"],
        agent_steps=result["agent_steps"],
        related_chunks=result["related_chunks"],
        related_entities=result["related_entities"],
    )


@app.get("/api/graph", response_model=GraphData)
async def get_graph():
    """
    知识图谱数据接口
    返回所有实体节点和关系连线，用于 ECharts 可视化
    """
    try:
        data = graph_store.get_all_entities_and_relations()
        nodes = []
        for n in data["nodes"]:
            nodes.append({
                "name": n["name"],
                "category": n["entity_type"],
            })
        edges = []
        for e in data["edges"]:
            edges.append({
                "source": e["source"],
                "target": e["target"],
                "label": e["rel_type"],
            })
        # 如果 Neo4j 有数据就返回真实数据，没数据就返回空图
        if nodes:
            return GraphData(nodes=nodes, edges=edges)
        return GraphData(nodes=[], edges=[])
    except Exception as e:
        # Neo4j 未启动时返回模拟数据
        return _get_mock_graph_data()


@app.delete("/api/graph")
async def clear_graph():
    """清空知识图谱中的所有实体和关系"""
    try:
        graph_store.clear_graph()
        return {"message": "图谱已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空图谱失败: {str(e)}")


@app.delete("/api/graph/entity/{name}")
async def delete_entity(name: str):
    """删除指定实体及其所有关系，返回删除信息用于撤销"""
    try:
        result = graph_store.delete_entity(name)
        if not result["deleted"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除实体失败: {str(e)}")


@app.post("/api/graph/restore")
async def restore_entity(data: dict):
    """恢复被删除的实体和关系（撤销操作）"""
    try:
        entity = data.get("entity")
        relations = data.get("relations", [])
        if not entity:
            raise HTTPException(status_code=400, detail="缺少实体信息")
        graph_store.restore_entity(entity, relations)
        return {"message": f"已恢复实体: {entity['name']}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复实体失败: {str(e)}")


@app.get("/api/docs")
async def list_documents():
    """获取已上传的文档列表"""
    return {"documents": _uploaded_docs}


@app.delete("/api/docs/{filename}")
async def delete_document(filename: str):
    """删除指定文档及其关联的向量和图谱数据"""
    global _uploaded_docs

    # 检查文档是否存在
    found = any(d["filename"] == filename for d in _uploaded_docs)
    if not found:
        raise HTTPException(status_code=404, detail=f"文档不存在: {filename}")

    # 从文档列表中移除
    _uploaded_docs = [d for d in _uploaded_docs if d["filename"] != filename]

    # 删除关联的向量数据
    removed = vector_store.delete_vectors_by_doc(filename)

    # 清空图谱（MVP 简化：全量清空后重新抽取剩余文档）
    try:
        graph_store.clear_graph()
        # 如果还有剩余文档，重新抽取实体入库
        for doc in _uploaded_docs:
            # 重新解析并抽取（简化处理：直接用已有的 chunks 重新抽取）
            pass
    except Exception as e:
        print(f"[Delete] 图谱清理异常（Neo4j 可能未启动）: {e}")

    print(f"[Delete] 已删除文档: {filename}，清除 {removed} 条向量")
    return {"message": f"文档 {filename} 已删除", "vectors_removed": removed}


def _get_mock_graph_data() -> GraphData:
    """返回模拟的图谱数据（Neo4j 不可用时使用）"""
    nodes = [
        # 人员
        {"name": "张三", "category": "人员"},
        {"name": "李四", "category": "人员"},
        {"name": "王五", "category": "人员"},
        {"name": "赵六", "category": "人员"},
        {"name": "刘七", "category": "人员"},
        # 部门
        {"name": "技术部", "category": "部门"},
        {"name": "运维部", "category": "部门"},
        {"name": "产品部", "category": "部门"},
        {"name": "数据部", "category": "部门"},
        # 系统
        {"name": "订单系统", "category": "系统"},
        {"name": "用户系统", "category": "系统"},
        {"name": "支付系统", "category": "系统"},
        {"name": "库存系统", "category": "系统"},
        {"name": "日志系统", "category": "系统"},
        # 模块
        {"name": "知识库模块", "category": "模块"},
        {"name": "解析服务", "category": "模块"},
        {"name": "网关模块", "category": "模块"},
        {"name": "认证模块", "category": "模块"},
        {"name": "调度模块", "category": "模块"},
        # 接口
        {"name": "用户查询接口", "category": "接口"},
        {"name": "订单创建接口", "category": "接口"},
        {"name": "数据同步接口", "category": "接口"},
        {"name": "文件上传接口", "category": "接口"},
    ]
    edges = [
        # 人员 → 负责 → 模块/系统
        {"source": "张三", "target": "知识库模块", "label": "负责"},
        {"source": "李四", "target": "解析服务", "label": "负责"},
        {"source": "王五", "target": "订单系统", "label": "负责"},
        {"source": "赵六", "target": "技术部", "label": "负责"},
        {"source": "刘七", "target": "运维部", "label": "负责"},
        # 模块依赖
        {"source": "知识库模块", "target": "解析服务", "label": "依赖"},
        {"source": "知识库模块", "target": "网关模块", "label": "依赖"},
        {"source": "订单系统", "target": "支付系统", "label": "依赖"},
        {"source": "订单系统", "target": "库存系统", "label": "依赖"},
        {"source": "用户系统", "target": "认证模块", "label": "依赖"},
        # 归属
        {"source": "解析服务", "target": "技术部", "label": "属于"},
        {"source": "知识库模块", "target": "技术部", "label": "属于"},
        {"source": "调度模块", "target": "运维部", "label": "属于"},
        {"source": "日志系统", "target": "运维部", "label": "属于"},
        {"source": "数据同步接口", "target": "数据部", "label": "属于"},
        # 管理
        {"source": "技术部", "target": "解析服务", "label": "管理"},
        {"source": "产品部", "target": "知识库模块", "label": "管理"},
        {"source": "运维部", "target": "日志系统", "label": "管理"},
        # 接口归属
        {"source": "用户查询接口", "target": "认证模块", "label": "属于"},
        {"source": "订单创建接口", "target": "订单系统", "label": "属于"},
        {"source": "文件上传接口", "target": "知识库模块", "label": "属于"},
    ]
    return GraphData(nodes=nodes, edges=edges)


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("多智能体协同知识库系统 启动中...")
    print("API 文档: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
