"""
数据模型定义
定义所有 API 接口的请求和响应数据结构
"""

from pydantic import BaseModel
from typing import List, Optional


class DocumentChunk(BaseModel):
    """文档切片"""
    chunk_id: int
    content: str
    start_pos: int
    end_pos: int


class UploadResponse(BaseModel):
    """文档上传响应"""
    filename: str
    file_type: str
    total_length: int
    chunk_count: int
    chunks: List[DocumentChunk]


class Entity(BaseModel):
    """实体"""
    name: str
    entity_type: str  # 人员、部门、系统、模块、接口


class Relation(BaseModel):
    """关系"""
    source: str
    target: str
    relation_type: str  # 负责、依赖、属于、管理


class ExtractResponse(BaseModel):
    """实体抽取响应"""
    entities: List[Entity]
    relations: List[Relation]
    entity_count: int
    relation_count: int


class EmbedResponse(BaseModel):
    """向量入库响应"""
    embedded_count: int
    collection_name: str
    dimension: int


class AgentStep(BaseModel):
    """智能体工作步骤"""
    agent_name: str
    status: str
    output: str


class ChatResponse(BaseModel):
    """智能问答响应"""
    question: str
    answer: str
    agent_steps: List[AgentStep]
    related_chunks: List[str]
    related_entities: List[dict]


class GraphData(BaseModel):
    """知识图谱数据"""
    nodes: List[dict]
    edges: List[dict]
