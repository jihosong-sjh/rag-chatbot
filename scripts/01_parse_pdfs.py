#!/usr/bin/env python3
"""PDF 파싱 파이프라인 실행 스크립트.

data/raw/ 에 있는 PDF 파일들을 파싱하여:
1. data/parsed/ 에 Markdown 파일 저장
2. data/chunks/ 에 메타데이터 부착된 JSON 청크 저장
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src.config import RAW_DIR, PARSED_DIR, CHUNKS_DIR
from src.parsing.pdf_extractor import extract_pdf, save_markdown
from src.parsing.structure_parser import parse_structure
from src.parsing.chunker import (
    DocumentMetadata,
    create_chunks,
    save_chunks,
    print_chunk_stats,
)

# ── 로깅 설정 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
console = Console()

# ── 보험사 메타데이터 매핑 ──
# 파일명 패턴으로 보험사를 식별
COMPANY_MAP: dict[str, str] = {
    "samsung": "삼성화재",
    "hyundai": "현대해상",
    "db": "DB손해보험",
    "kb": "KB손해보험",
    "meritz": "메리츠화재",
    "standard": "금감원(표준약관)",
}


def detect_company(filename: str) -> str:
    """파일명에서 보험사를 식별한다."""
    lower = filename.lower()
    for key, name in COMPANY_MAP.items():
        if key in lower:
            return name
    return "알 수 없음"


def find_pdfs() -> list[Path]:
    """data/raw/ 하위의 모든 PDF 파일을 찾는다."""
    pdfs = sorted(RAW_DIR.rglob("*.pdf"))
    if not pdfs:
        console.print(
            f"[bold red]PDF 파일을 찾을 수 없습니다.[/bold red]\n"
            f"[dim]{RAW_DIR}/ 하위에 보험약관 PDF 파일을 넣어주세요.[/dim]\n\n"
            f"예시 디렉토리 구조:\n"
            f"  data/raw/companies/samsung_fire/samsung_fire_silson_2025.pdf\n"
            f"  data/raw/companies/db_insurance/db_silson_2025.pdf\n"
            f"  data/raw/standard/standard_silson_2025.pdf",
        )
    return pdfs


def process_single_pdf(pdf_path: Path) -> dict | None:
    """단일 PDF를 처리하여 Markdown과 청크를 생성한다."""
    console.print(f"\n[bold blue]▶ 처리 중: {pdf_path.name}[/bold blue]")

    try:
        # 1. PDF 텍스트 추출
        result = extract_pdf(pdf_path)
        console.print(f"  ✓ 텍스트 추출 완료 ({result.total_pages} 페이지, 스캔 {result.scanned_ratio*100:.1f}%)")

        if result.is_mostly_scanned:
            console.print(
                "  [yellow]⚠ 스캔 비율이 높아 텍스트 품질이 낮을 수 있습니다.[/yellow]"
            )

        # 2. Markdown 저장
        md_path = save_markdown(result, PARSED_DIR)
        console.print(f"  ✓ Markdown 저장: {md_path.name}")

        # 3. 약관 구조 파싱
        nodes = parse_structure(result.markdown)
        console.print(f"  ✓ 구조 파싱: {len(nodes)}개 노드")

        if not nodes:
            console.print("  [yellow]⚠ 파싱된 노드가 없습니다. 약관 구조가 감지되지 않았습니다.[/yellow]")
            return None

        # 4. 청킹
        company = detect_company(pdf_path.name)
        doc_meta = DocumentMetadata(
            insurance_company=company,
            product_type="실손의료보험",
            document_type="보통약관",
            source_file=pdf_path.name,
        )

        chunks = create_chunks(nodes, doc_meta)
        console.print(f"  ✓ 청킹: {len(chunks)}개 청크")

        # 5. 청크 저장
        chunks_path = save_chunks(chunks, CHUNKS_DIR)
        console.print(f"  ✓ 청크 저장: {chunks_path.name}")

        # 6. 통계 출력
        print_chunk_stats(chunks)

        return {
            "file": pdf_path.name,
            "company": company,
            "pages": result.total_pages,
            "scanned_ratio": result.scanned_ratio,
            "nodes": len(nodes),
            "chunks": len(chunks),
        }

    except Exception:
        console.print(f"  [bold red]✗ 처리 실패[/bold red]")
        logger.exception("PDF 처리 실패: %s", pdf_path)
        return None


def main() -> None:
    """메인 실행 함수."""
    console.print("[bold]보험약관 PDF 파싱 파이프라인[/bold]\n")

    pdfs = find_pdfs()
    if not pdfs:
        sys.exit(1)

    console.print(f"발견된 PDF: {len(pdfs)}개\n")
    for p in pdfs:
        console.print(f"  • {p.relative_to(RAW_DIR)}")

    # 각 PDF 처리
    results = []
    for pdf_path in pdfs:
        result = process_single_pdf(pdf_path)
        if result:
            results.append(result)

    # 전체 결과 요약
    if results:
        console.print("\n[bold green]━━━ 전체 결과 요약 ━━━[/bold green]\n")

        table = Table(title="PDF 파싱 결과")
        table.add_column("파일", style="cyan")
        table.add_column("보험사", style="magenta")
        table.add_column("페이지", justify="right")
        table.add_column("스캔%", justify="right")
        table.add_column("노드", justify="right")
        table.add_column("청크", justify="right", style="green")

        for r in results:
            table.add_row(
                r["file"],
                r["company"],
                str(r["pages"]),
                f"{r['scanned_ratio']*100:.0f}%",
                str(r["nodes"]),
                str(r["chunks"]),
            )

        console.print(table)

        total_chunks = sum(r["chunks"] for r in results)
        console.print(f"\n총 {len(results)}개 PDF → {total_chunks}개 청크 생성 완료")
    else:
        console.print("\n[bold red]처리된 PDF가 없습니다.[/bold red]")


if __name__ == "__main__":
    main()
