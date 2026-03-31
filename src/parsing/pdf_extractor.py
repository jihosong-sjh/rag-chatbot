"""PDF 텍스트 추출기.

pymupdf4llm으로 PDF를 Markdown으로 변환하고,
pdfplumber로 표(table)를 보완 추출한다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf4llm
import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """단일 페이지 추출 결과."""

    page_number: int
    text: str
    tables: list[list[list[str | None]]] = field(default_factory=list)
    is_scanned: bool = False


@dataclass
class PDFExtractionResult:
    """PDF 전체 추출 결과."""

    source_file: str
    total_pages: int
    pages: list[PageInfo]
    markdown: str
    scanned_ratio: float = 0.0

    @property
    def is_mostly_scanned(self) -> bool:
        return self.scanned_ratio > 0.5


def detect_scanned_page(page_text: str, threshold: int = 50) -> bool:
    """페이지가 스캔 이미지인지 판별한다.

    텍스트 추출 결과가 threshold 글자 미만이면 스캔으로 간주.
    """
    cleaned = page_text.strip()
    return len(cleaned) < threshold


def extract_tables_with_pdfplumber(pdf_path: str | Path) -> dict[int, list[list[list[str | None]]]]:
    """pdfplumber로 페이지별 표를 추출한다.

    Returns:
        {페이지번호(0-based): [표1, 표2, ...]} 형태의 딕셔너리.
        각 표는 [[row1_cells], [row2_cells], ...] 형태.
    """
    tables_by_page: dict[int, list[list[list[str | None]]]] = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                if page_tables:
                    tables_by_page[i] = page_tables
    except Exception:
        logger.exception("pdfplumber 표 추출 실패: %s", pdf_path)

    return tables_by_page


def table_to_markdown(table: list[list[str | None]]) -> str:
    """2차원 표 데이터를 Markdown 테이블 문자열로 변환한다."""
    if not table or not table[0]:
        return ""

    rows = []
    for row in table:
        cells = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        rows.append("| " + " | ".join(cells) + " |")

    if len(rows) >= 1:
        # 첫 행을 헤더로 간주하고 구분선 추가
        header = rows[0]
        separator = "| " + " | ".join(["---"] * len(table[0])) + " |"
        return header + "\n" + separator + "\n" + "\n".join(rows[1:])

    return "\n".join(rows)


def extract_pdf(pdf_path: str | Path) -> PDFExtractionResult:
    """PDF에서 텍스트와 표를 추출한다.

    1단계: pymupdf4llm으로 전체 Markdown 변환
    2단계: pdfplumber로 표 보완 추출
    3단계: 스캔 페이지 비율 계산

    Args:
        pdf_path: PDF 파일 경로.

    Returns:
        PDFExtractionResult 객체.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    logger.info("PDF 추출 시작: %s", pdf_path.name)

    # 1단계: pymupdf4llm으로 Markdown 변환
    md_text = pymupdf4llm.to_markdown(str(pdf_path))

    # 페이지별 추출 (메타데이터용)
    page_chunks = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)

    # 2단계: pdfplumber로 표 보완 추출
    tables_by_page = extract_tables_with_pdfplumber(pdf_path)

    # 3단계: 페이지별 정보 구성
    pages: list[PageInfo] = []
    scanned_count = 0

    for chunk in page_chunks:
        page_num = chunk["metadata"]["page"]
        page_text = chunk["text"]
        is_scanned = detect_scanned_page(page_text)

        if is_scanned:
            scanned_count += 1

        page_tables = tables_by_page.get(page_num, [])

        pages.append(
            PageInfo(
                page_number=page_num,
                text=page_text,
                tables=page_tables,
                is_scanned=is_scanned,
            )
        )

    total_pages = len(pages)
    scanned_ratio = scanned_count / total_pages if total_pages > 0 else 0.0

    if scanned_ratio > 0.2:
        logger.warning(
            "스캔 페이지 비율이 높습니다: %.1f%% (%d/%d 페이지)",
            scanned_ratio * 100,
            scanned_count,
            total_pages,
        )

    logger.info(
        "PDF 추출 완료: %s (%d 페이지, 스캔 비율 %.1f%%)",
        pdf_path.name,
        total_pages,
        scanned_ratio * 100,
    )

    return PDFExtractionResult(
        source_file=pdf_path.name,
        total_pages=total_pages,
        pages=pages,
        markdown=md_text,
        scanned_ratio=scanned_ratio,
    )


def save_markdown(result: PDFExtractionResult, output_dir: str | Path) -> Path:
    """추출 결과를 Markdown 파일로 저장한다."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(result.source_file).stem
    output_path = output_dir / f"{stem}.md"
    output_path.write_text(result.markdown, encoding="utf-8")

    logger.info("Markdown 저장: %s", output_path)
    return output_path
