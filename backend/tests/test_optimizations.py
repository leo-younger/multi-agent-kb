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


from services.entity_extractor import extract_from_chunks, extract_entities_from_text


def test_extract_entities_dedup():
    """多个切片中的重复实体应去重"""
    chunks = ["张三负责知识库模块", "张三也负责解析服务", "李四负责订单系统"]
    entities, relations = extract_from_chunks(chunks)
    names = [e.name for e in entities]
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
    assert len(entities) > 0


from unittest.mock import patch, MagicMock


def test_search_related_entities_empty_keywords():
    """空关键词列表应返回空结果"""
    from services.graph_store import search_related_entities
    result = search_related_entities([])
    assert result == []


@patch("services.graph_store._get_driver")
def test_search_related_entities_calls_unwind(mock_get_driver):
    """查询应使用 UNWIND 合并关键词"""
    from services.graph_store import search_related_entities
    mock_driver = MagicMock()
    mock_get_driver.return_value = mock_driver

    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([
        {"source": "张三", "target": "知识库模块", "rel_type": "负责"},
    ]))
    mock_session.run.return_value = mock_result

    result = search_related_entities(["张三", "知识库模块"])

    # 验证调用了 session.run 且参数包含 keywords 列表
    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args
    assert "keywords" in call_args.kwargs or "keywords" in call_args[1]
    # 验证 Cypher 包含 UNWIND
    cypher = call_args[0][0]
    assert "UNWIND" in cypher


import asyncio
from services.agents import run_agent_pipeline, _analyze_question, _extract_keywords


def test_analyze_question():
    """问题类型识别正确"""
    assert _analyze_question("张三负责什么模块？") == "职责查询"
    assert _analyze_question("订单系统依赖哪些服务？") == "依赖关系查询"
    assert _analyze_question("解析服务属于哪个部门？") == "归属查询"
    assert _analyze_question("随便聊聊") == "通用查询"


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
