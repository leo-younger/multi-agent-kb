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
