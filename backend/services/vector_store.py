"""
向量存储服务
使用 numpy 实现内存向量检索（余弦相似度）
MVP 阶段替代 Milvus，无需额外依赖
"""

import numpy as np
from typing import List, Dict

# 内存向量存储
_vectors: np.ndarray = None       # 向量矩阵 (N, dim)
_texts: List[str] = []            # 对应文本
_doc_names: List[str] = []        # 对应文档名
_dimension: int = 384             # 向量维度


def create_collection(dimension: int = 384):
    """
    初始化向量存储（清空旧数据）

    Args:
        dimension: 向量维度
    """
    global _vectors, _texts, _doc_names, _dimension
    _vectors = None
    _texts = []
    _doc_names = []
    _dimension = dimension
    print(f"[VectorStore] 向量存储初始化，维度={dimension}")


def insert_vectors(vectors: List[List[float]], texts: List[str], doc_name: str) -> int:
    """
    将向量和对应文本存入内存

    Args:
        vectors: 向量列表
        texts: 对应的文本片段
        doc_name: 来源文档名

    Returns:
        插入的记录数
    """
    global _vectors

    vec_array = np.array(vectors, dtype=np.float32)

    if _vectors is None:
        _vectors = vec_array
    else:
        _vectors = np.vstack([_vectors, vec_array])

    _texts.extend(texts)
    _doc_names.extend([doc_name] * len(texts))

    print(f"[VectorStore] 插入 {len(vectors)} 条向量，来自文档 {doc_name}，总计 {_vectors.shape[0]} 条")
    return len(vectors)


def search_vectors(query_vector: List[float], top_k: int = 3) -> List[dict]:
    """
    搜索最相似的向量（余弦相似度）

    Args:
        query_vector: 查询向量
        top_k: 返回最相似的前 k 条

    Returns:
        搜索结果列表，每项包含 text, doc_name, distance
    """
    if _vectors is None or len(_texts) == 0:
        return []

    query = np.array(query_vector, dtype=np.float32)

    # 计算余弦相似度
    # sim = (A · B) / (||A|| * ||B||)
    dot_products = _vectors @ query
    norms = np.linalg.norm(_vectors, axis=1) * np.linalg.norm(query)
    # 避免除零
    norms = np.where(norms == 0, 1e-10, norms)
    similarities = dot_products / norms

    # 取 top_k
    top_k = min(top_k, len(similarities))
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "text": _texts[idx],
            "doc_name": _doc_names[idx],
            "distance": float(similarities[idx]),
        })

    return results


def delete_vectors_by_doc(doc_name: str) -> int:
    """
    删除指定文档的所有向量

    Args:
        doc_name: 文档名

    Returns:
        删除的记录数
    """
    global _vectors, _texts, _doc_names

    if _vectors is None or not _doc_names:
        return 0

    indices_to_keep = [i for i, name in enumerate(_doc_names) if name != doc_name]
    removed = len(_doc_names) - len(indices_to_keep)

    if removed == 0:
        return 0

    if indices_to_keep:
        _vectors = _vectors[indices_to_keep]
        _texts = [_texts[i] for i in indices_to_keep]
        _doc_names = [_doc_names[i] for i in indices_to_keep]
    else:
        _vectors = None
        _texts = []
        _doc_names = []

    print(f"[VectorStore] 删除文档 {doc_name} 的 {removed} 条向量，剩余 {len(_texts)} 条")
    return removed


def get_collection_stats() -> dict:
    """获取存储统计信息"""
    return {
        "exists": _vectors is not None,
        "total_vectors": _vectors.shape[0] if _vectors is not None else 0,
        "dimension": _dimension,
    }
