"""
PDF 매뉴얼 로더.
manuals/ 폴더의 모든 PDF를 텍스트로 변환하여 Claude 시스템 프롬프트에 포함.
서버 시작 시 한 번만 실행.
"""

import pathlib
import logging

logger = logging.getLogger(__name__)


def load_manuals() -> str:
    """
    manuals/ 폴더의 모든 PDF를 텍스트로 변환.

    Returns:
        str: 파일명과 함께 포맷된 매뉴얼 텍스트. 파일이 없으면 빈 문자열.
    """
    manuals_dir = pathlib.Path("manuals")

    if not manuals_dir.exists():
        logger.info("manuals/ folder does not exist. Skipping manual loading.")
        return ""

    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning(
            "pypdf is not installed. Install with: pip install pypdf\n"
            "Manuals will not be loaded."
        )
        return ""

    texts = []
    pdf_files = sorted(manuals_dir.glob("*.pdf"))

    if not pdf_files:
        logger.info("No PDF files found in manuals/ folder.")
        return ""

    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading manual: {pdf_path.name}")
            reader = PdfReader(str(pdf_path))

            text = "\n".join(
                page.extract_text()
                for page in reader.pages
                if page.extract_text()
            )

            if text.strip():
                # 파일명을 헤더로 추가
                section = f"### {pdf_path.stem}\n{text.strip()}"
                texts.append(section)
                logger.info(f"  ✓ Loaded {len(reader.pages)} pages")
            else:
                logger.warning(f"  ✗ No text extracted from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error loading {pdf_path.name}: {e}")
            continue

    result = "\n\n".join(texts)
    logger.info(f"Total manuals loaded: {len(texts)} files")
    return result
