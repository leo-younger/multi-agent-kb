"""优化项测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.document_parser import chunk_text
from services.embedding import get_embedding, get_embeddings, get_dimension


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
    # 所有切片应覆盖全文的每个位置
    covered = set()
    for c in chunks:
        covered.update(range(c.start_pos, c.end_pos))
    assert covered == set(range(len(text)))


def test_chunk_single():
    """文本长度 <= chunk_size 时只有 1 个切片"""
    text = "Hello"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].content == "Hello"


def test_embedding_mock_fallback():
    """mock 模式应返回 384 维归一化向量"""
    from services.embedding import _text_to_mock_vector
    vec = _text_to_mock_vector("测试文本")
    assert len(vec) == 384
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
