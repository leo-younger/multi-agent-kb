"""
图数据库服务
使用 Neo4j 存储和查询实体关系图谱
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional

# Neo4j 连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

_driver = None


def _get_driver():
    """获取 Neo4j 驱动实例"""
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # 验证连接
            _driver.verify_connectivity()
            print("[GraphStore] Neo4j 连接成功")
        except Exception as e:
            print(f"[GraphStore] Neo4j 连接失败: {e}")
            raise
    return _driver


def clear_graph():
    """清空图数据库中的所有节点和关系"""
    driver = _get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("[GraphStore] 图数据已清空")


def create_entity(name: str, entity_type: str):
    """
    创建实体节点

    Args:
        name: 实体名称
        entity_type: 实体类型（人员、部门、系统、模块、接口）
    """
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            "MERGE (e:Entity {name: $name}) "
            "SET e.entity_type = $entity_type",
            name=name, entity_type=entity_type,
        )


def create_relation(source: str, target: str, relation_type: str):
    """
    创建实体间关系

    Args:
        source: 源实体名称
        target: 目标实体名称
        relation_type: 关系类型（负责、依赖、属于、管理）
    """
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            "MATCH (a:Entity {name: $source}), (b:Entity {name: $target}) "
            "MERGE (a)-[r:RELATION {type: $rel_type}]->(b)",
            source=source, target=target, rel_type=relation_type,
        )


def get_entity_relations(entity_name: str) -> List[Dict]:
    """
    查询指定实体的所有关系

    Args:
        entity_name: 实体名称

    Returns:
        关系列表，每项包含 source, target, relation_type
    """
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (a:Entity {name: $name})-[r:RELATION]->(b:Entity) "
            "RETURN a.name AS source, b.name AS target, r.type AS rel_type "
            "UNION "
            "MATCH (b:Entity)-[r:RELATION]->(a:Entity {name: $name}) "
            "RETURN b.name AS source, a.name AS target, r.type AS rel_type",
            name=entity_name,
        )
        return [dict(record) for record in result]


def get_all_entities_and_relations() -> Dict:
    """
    获取所有实体和关系，用于知识图谱可视化

    Returns:
        {"nodes": [...], "edges": [...]}
    """
    driver = _get_driver()
    with driver.session() as session:
        # 获取所有实体
        nodes_result = session.run(
            "MATCH (e:Entity) RETURN e.name AS name, e.entity_type AS entity_type"
        )
        nodes = [dict(record) for record in nodes_result]

        # 获取所有关系
        edges_result = session.run(
            "MATCH (a:Entity)-[r:RELATION]->(b:Entity) "
            "RETURN a.name AS source, b.name AS target, r.type AS rel_type"
        )
        edges = [dict(record) for record in edges_result]

    return {"nodes": nodes, "edges": edges}


def delete_entity(name: str) -> Dict:
    """
    删除指定实体及其所有关系

    Args:
        name: 实体名称

    Returns:
        删除结果，包含被删除的实体信息和关系数
    """
    driver = _get_driver()
    with driver.session() as session:
        # 先查询要删除的实体和关系（用于撤销）
        entity_result = session.run(
            "MATCH (e:Entity {name: $name}) RETURN e.name AS name, e.entity_type AS entity_type",
            name=name,
        )
        entity_record = entity_result.single()
        if not entity_record:
            return {"deleted": False, "message": f"实体 {name} 不存在"}

        entity_info = {"name": entity_record["name"], "entity_type": entity_record["entity_type"]}

        # 查询关联关系
        rels_result = session.run(
            "MATCH (a:Entity {name: $name})-[r:RELATION]->(b:Entity) "
            "RETURN a.name AS source, b.name AS target, r.type AS rel_type "
            "UNION "
            "MATCH (b:Entity)-[r:RELATION]->(a:Entity {name: $name}) "
            "RETURN b.name AS source, a.name AS target, r.type AS rel_type",
            name=name,
        )
        relations = [dict(record) for record in rels_result]

        # 删除实体及其关系
        session.run("MATCH (e:Entity {name: $name}) DETACH DELETE e", name=name)

    print(f"[GraphStore] 已删除实体: {name}，关联 {len(relations)} 条关系")
    return {"deleted": True, "entity": entity_info, "relations": relations}


def restore_entity(entity: Dict, relations: List[Dict]):
    """
    恢复被删除的实体和关系（用于撤销）

    Args:
        entity: 实体信息 {"name": ..., "entity_type": ...}
        relations: 关系列表 [{"source": ..., "target": ..., "rel_type": ...}]
    """
    driver = _get_driver()
    create_entity(entity["name"], entity["entity_type"])
    for r in relations:
        # 确保两端实体都存在
        create_entity(r["source"], "未知")
        create_entity(r["target"], "未知")
        create_relation(r["source"], r["target"], r["rel_type"])
    print(f"[GraphStore] 已恢复实体: {entity['name']}，关系 {len(relations)} 条")


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
