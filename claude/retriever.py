"""
벡터 검색을 통해 관련 매뉴얼 청크를 검색하는 리트리버.
"""

import sqlite3
import json
import logging
import math
from typing import List

logger = logging.getLogger(__name__)

DB_PATH = "manuals.db"


def _get_db_connection():
    """SQLite 연결."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


async def retrieve_manuals(query: str, top_k: int = 3) -> str:
    """
    사용자 질문에 관련된 매뉴얼 청크를 검색.

    Args:
        query: 사용자 질문
        top_k: 반환할 청크 개수

    Returns:
        관련 청크들을 포맷한 텍스트
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("sentence-transformers not installed")
        return ""

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        # 테이블 존재 확인
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
        )
        if not cursor.fetchone():
            logger.info("Chunks table not found. No manuals loaded yet.")
            conn.close()
            return ""

        # 쿼리 임베딩 생성
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode([query], convert_to_numpy=True)[0].tolist()

        # 모든 청크 가져오기 (임베딩과 함께)
        cursor.execute("SELECT id, text, embedding FROM chunks ORDER BY filename, chunk_index")
        rows = cursor.fetchall()

        if not rows:
            logger.info("No chunks found in database")
            conn.close()
            return ""

        # 유사도 계산
        similarities = []
        for row in rows:
            embedding = json.loads(row["embedding"])
            similarity = _cosine_similarity(query_embedding, embedding)
            similarities.append((row["id"], row["text"], similarity))

        # Top-K 선택
        top_results = sorted(similarities, key=lambda x: x[2], reverse=True)[:top_k]

        if not top_results:
            return ""

        # 포맷
        context_parts = []
        for _, text, score in top_results:
            if score > 0.1:  # 유사도 임계값
                context_parts.append(f"{text}\n")

        conn.close()

        if context_parts:
            return "## 참고 매뉴얼\n" + "---\n".join(context_parts)
        else:
            return ""

    except Exception as e:
        logger.error(f"Error retrieving manuals: {e}")
        return ""
