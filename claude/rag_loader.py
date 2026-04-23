"""
RAG (Retrieval Augmented Generation) 매뉴얼 로더.
PDF를 청크로 분할하고, sentence-transformers로 임베딩을 생성.
SQLite에 저장하여 벡터 검색에 사용.
서버 시작 시 한 번만 실행.
"""

import pathlib
import sqlite3
import logging
import json
from typing import List

logger = logging.getLogger(__name__)

DB_PATH = "manuals.db"


def _get_db_connection():
    """SQLite 연결."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _create_tables():
    """SQLite 테이블 생성."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_filename ON chunks(filename)
    """)

    conn.commit()
    conn.close()


def _split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    텍스트를 청크로 분할.

    Args:
        text: 원본 텍스트
        chunk_size: 청크 크기 (문자)
        overlap: 청크 간 겹침 (문자)

    Returns:
        청크 리스트
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


def _get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    텍스트 리스트의 임베딩 생성 (sentence-transformers 사용).

    Args:
        texts: 텍스트 리스트

    Returns:
        임베딩 벡터 리스트
    """
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    except ImportError:
        logger.error("sentence-transformers not installed")
        return []


def load_pdf_to_db():
    """
    manuals/ 폴더의 모든 PDF를 로드하고 임베딩을 생성하여 DB에 저장.
    """
    manuals_dir = pathlib.Path("manuals")
    if not manuals_dir.exists():
        logger.info("manuals/ folder does not exist")
        return

    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf not installed")
        return

    _create_tables()
    conn = _get_db_connection()
    cursor = conn.cursor()

    # 기존 데이터 확인 (다시 로드하지 않으려면)
    cursor.execute("SELECT COUNT(*) as cnt FROM chunks")
    existing_count = cursor.fetchone()["cnt"]

    pdf_files = sorted(manuals_dir.glob("*.pdf"))

    if existing_count > 0 and len(pdf_files) > 0:
        logger.info(f"Manuals already loaded ({existing_count} chunks). Skipping.")
        conn.close()
        return

    logger.info(f"Loading {len(pdf_files)} PDF files into database...")

    for pdf_path in pdf_files:
        try:
            logger.info(f"  Processing: {pdf_path.name}")
            reader = PdfReader(str(pdf_path))

            text = "\n".join(
                page.extract_text() for page in reader.pages
                if page.extract_text()
            )

            if not text.strip():
                logger.warning(f"    No text extracted from {pdf_path.name}")
                continue

            # 청크 분할
            chunks = _split_into_chunks(text)
            logger.info(f"    Split into {len(chunks)} chunks")

            # 임베딩 생성
            embeddings = _get_embeddings(chunks)

            if not embeddings:
                logger.warning(f"    Failed to generate embeddings for {pdf_path.name}")
                continue

            # DB에 저장
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_blob = json.dumps(embedding)
                cursor.execute(
                    """
                    INSERT INTO chunks (filename, chunk_index, text, embedding)
                    VALUES (?, ?, ?, ?)
                    """,
                    (pdf_path.name, idx, chunk, embedding_blob),
                )

            conn.commit()
            logger.info(f"    ✓ Saved {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"  Error processing {pdf_path.name}: {e}")
            continue

    conn.close()
    logger.info("Finished loading manuals into database")
