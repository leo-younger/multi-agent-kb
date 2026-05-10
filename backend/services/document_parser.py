"""
文档解析服务
支持 PDF、Word、TXT 文件的解析和文本切片
"""

import io
from typing import List
from PyPDF2 import PdfReader
from docx import Document
from models.schemas import DocumentChunk


def parse_pdf(file_content: bytes) -> str:
    """解析 PDF 文件，提取文本内容"""
    reader = PdfReader(io.BytesIO(file_content))
    return "".join(page.extract_text() or "" for page in reader.pages)


def parse_docx(file_content: bytes) -> str:
    """解析 Word 文件，提取文本内容"""
    doc = Document(io.BytesIO(file_content))
    return "\n".join(para.text for para in doc.paragraphs)


def parse_txt(file_content: bytes) -> str:
    """解析 TXT 文件"""
    return file_content.decode("utf-8", errors="ignore")


def parse_document(filename: str, file_content: bytes) -> str:
    """
    根据文件类型选择对应的解析器
    支持: .pdf, .docx, .doc, .txt
    """
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return parse_pdf(file_content)
    elif ext in ("docx", "doc"):
        return parse_docx(file_content)
    elif ext == "txt":
        return parse_txt(file_content)
    else:
        raise ValueError(f"不支持的文件类型: .{ext}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[DocumentChunk]:
    """
    将文本切分为固定大小的片段，支持重叠

    Args:
        text: 原始文本
        chunk_size: 每个切片的字符数（默认 500）
        overlap: 切片之间的重叠字符数（默认 100）

    Returns:
        文档切片列表
    """
    if overlap >= chunk_size:
        overlap = 0

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            content=text[start:end],
            start_pos=start,
            end_pos=end,
        )
        chunks.append(chunk)
        chunk_id += 1
        # 下一个切片的起始位置 = 当前结束位置 - 重叠长度
        start = end - overlap
        if end >= len(text):
            break

    return chunks
