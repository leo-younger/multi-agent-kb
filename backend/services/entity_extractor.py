"""
实体关系抽取服务
使用规则匹配 + 预置 mock 数据进行实体和关系抽取
不依赖大模型，适合 MVP 演示
"""

import re
from typing import List, Tuple
from models.schemas import Entity, Relation

# 预置实体词典
ENTITY_PATTERNS = {
    "人员": ["张三", "李四", "王五", "赵六", "刘七"],
    "部门": ["技术部", "产品部", "运维部", "测试部", "数据部"],
    "系统": ["订单系统", "用户系统", "支付系统", "库存系统", "日志系统"],
    "模块": ["知识库模块", "解析服务", "网关模块", "认证模块", "调度模块"],
    "接口": ["用户查询接口", "订单创建接口", "数据同步接口", "文件上传接口"],
}

# 预置关系模板
RELATION_TEMPLATES = [
    ("张三", "知识库模块", "负责"),
    ("李四", "解析服务", "负责"),
    ("王五", "订单系统", "负责"),
    ("知识库模块", "解析服务", "依赖"),
    ("知识库模块", "网关模块", "依赖"),
    ("订单系统", "支付系统", "依赖"),
    ("解析服务", "技术部", "属于"),
    ("知识库模块", "技术部", "属于"),
    ("技术部", "解析服务", "管理"),
    ("产品部", "知识库模块", "管理"),
    ("用户系统", "认证模块", "依赖"),
    ("认证模块", "用户查询接口", "属于"),
    ("订单创建接口", "订单系统", "属于"),
    ("数据同步接口", "数据部", "属于"),
    ("日志系统", "运维部", "属于"),
    ("调度模块", "运维部", "属于"),
    ("库存系统", "订单系统", "依赖"),
]


def extract_entities_from_text(text: str) -> List[Entity]:
    """
    从文本中提取实体（基于词典匹配）

    Args:
        text: 输入文本

    Returns:
        实体列表
    """
    found_entities = []
    seen = set()

    for entity_type, names in ENTITY_PATTERNS.items():
        for name in names:
            if name in text and name not in seen:
                found_entities.append(Entity(name=name, entity_type=entity_type))
                seen.add(name)

    # 如果文本中没有匹配到任何预置实体，返回默认的示例实体
    if not found_entities:
        found_entities = _get_default_entities()

    return found_entities


def extract_relations_from_text(text: str, entities: List[Entity]) -> List[Relation]:
    """
    从文本和实体中提取关系

    Args:
        text: 输入文本
        entities: 已提取的实体列表

    Returns:
        关系列表
    """
    entity_names = {e.name for e in entities}
    found_relations = []

    for src, tgt, rel_type in RELATION_TEMPLATES:
        if src in entity_names and tgt in entity_names:
            found_relations.append(
                Relation(source=src, target=tgt, relation_type=rel_type)
            )

    # 如果没有匹配到关系，返回默认示例
    if not found_relations:
        found_relations = _get_default_relations()

    return found_relations


def extract_from_chunks(chunks: List[str]) -> Tuple[List[Entity], List[Relation]]:
    """
    从多个文档切片中抽取实体和关系（合并去重）

    Args:
        chunks: 文本切片列表

    Returns:
        (实体列表, 关系列表)
    """
    all_entities = {}
    all_relations = {}

    for chunk in chunks:
        entities = extract_entities_from_text(chunk)
        for e in entities:
            all_entities[e.name] = e

        relations = extract_relations_from_text(chunk, entities)
        for r in relations:
            key = (r.source, r.target, r.relation_type)
            all_relations[key] = r

    return list(all_entities.values()), list(all_relations.values())


def _get_default_entities() -> List[Entity]:
    """返回默认示例实体"""
    return [
        Entity(name="张三", entity_type="人员"),
        Entity(name="李四", entity_type="人员"),
        Entity(name="技术部", entity_type="部门"),
        Entity(name="知识库模块", entity_type="模块"),
        Entity(name="解析服务", entity_type="模块"),
        Entity(name="订单系统", entity_type="系统"),
    ]


def _get_default_relations() -> List[Relation]:
    """返回默认示例关系"""
    return [
        Relation(source="张三", target="知识库模块", relation_type="负责"),
        Relation(source="李四", target="解析服务", relation_type="负责"),
        Relation(source="知识库模块", target="解析服务", relation_type="依赖"),
        Relation(source="解析服务", target="技术部", relation_type="属于"),
        Relation(source="技术部", target="解析服务", relation_type="管理"),
    ]
