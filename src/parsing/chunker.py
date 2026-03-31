"""구조 기반 청킹 엔진.

파싱된 약관 구조(StructureNode)를 기반으로
메타데이터가 부착된 청크를 생성한다.
"""

from __future__ import annotations

import json
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from src.config import settings
from src.parsing.structure_parser import (
    NodeType,
    StructureNode,
    get_part_label,
)

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """메타데이터가 부착된 청크."""

    chunk_id: str
    text: str
    token_count: int

    # 문서 메타데이터
    insurance_company: str
    product_type: str
    document_type: str
    source_file: str

    # 구조 메타데이터
    node_type: str  # article, appendix
    part: str  # "제2관 보험금의 지급"
    number: str  # "제10조"
    title: str  # "(보험금의 종류와 지급사유)"
    hierarchy_path: str  # "보통약관 > 제2관 > 제10조"

    # 참조 메타데이터
    references_to: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    """한국어 텍스트의 토큰 수를 추정한다.

    한국어는 BPE 토크나이저에서 1글자 ≈ 2~3 토큰.
    보수적으로 글자 수 × 1.5로 추정한다.
    """
    # 공백/줄바꿈 제외한 글자 수 기반
    char_count = len(text.replace(" ", "").replace("\n", ""))
    return max(int(char_count * 1.5), len(text.split()))


def generate_chunk_id(source_file: str, number: str, suffix: str = "") -> str:
    """청크 ID를 생성한다.

    예: "samsung_fire_silson_2025_art10" 또는 "samsung_fire_silson_2025_art10_p2"
    """
    stem = Path(source_file).stem
    # 번호에서 숫자만 추출
    num_clean = number.replace("제", "").replace("조", "").replace("관", "")
    num_clean = num_clean.replace("의", "x").replace(" ", "").strip()

    if "별표" in number:
        label = f"appendix{num_clean.replace('별표', '')}"
    else:
        label = f"art{num_clean}"

    chunk_id = f"{stem}_{label}"
    if suffix:
        chunk_id = f"{chunk_id}_{suffix}"

    return chunk_id


def split_long_article(node: StructureNode, max_tokens: int) -> list[tuple[str, str]]:
    """긴 조항을 항(Paragraph) 단위로 분할한다.

    Returns:
        [(suffix, text), ...] 형태의 리스트.
        suffix는 "p1", "p2" 등이고, text는 해당 항의 텍스트.
    """
    import re

    # 항(①, ②, ...) 기준으로 분할
    paragraph_pattern = re.compile(
        r"(?=(?:^|\n)([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]))"
    )

    parts = paragraph_pattern.split(node.text)

    if len(parts) <= 1:
        # 항이 없으면 그냥 텍스트를 균등 분할
        text = node.text
        mid = len(text) // 2
        # 줄바꿈 기준으로 가장 가까운 위치에서 분할
        newline_pos = text.find("\n", mid)
        if newline_pos == -1:
            newline_pos = mid
        return [("p1", text[:newline_pos].strip()), ("p2", text[newline_pos:].strip())]

    # 첫 부분 (조 제목 + ① 이전 텍스트)
    header = parts[0].strip()
    results: list[tuple[str, str]] = []
    paragraph_idx = 0

    i = 1
    while i < len(parts):
        marker = parts[i] if i < len(parts) else ""
        body = parts[i + 1] if i + 1 < len(parts) else ""
        paragraph_idx += 1

        # 조 제목을 각 청크 앞에 반복 삽입
        first_line = node.text.split("\n")[0]
        paragraph_text = f"{first_line}\n\n{marker} {body}".strip()

        results.append((f"p{paragraph_idx}", paragraph_text))
        i += 2

    # 분할 결과가 여전히 없으면 헤더만 반환
    if not results and header:
        results.append(("p1", header))

    return results


def merge_short_nodes(
    nodes: list[StructureNode],
    min_tokens: int,
) -> list[list[StructureNode]]:
    """짧은 조항을 인접 조항과 그룹으로 병합한다.

    Returns:
        [[node1], [node2, node3], [node4], ...] 형태.
        각 내부 리스트가 하나의 청크가 된다.
    """
    groups: list[list[StructureNode]] = []
    current_group: list[StructureNode] = []
    current_tokens = 0

    for node in nodes:
        node_tokens = estimate_tokens(node.text)

        if current_group and current_tokens + node_tokens > settings.chunk_max_tokens:
            # 현재 그룹을 확정하고 새 그룹 시작
            groups.append(current_group)
            current_group = [node]
            current_tokens = node_tokens
        elif node_tokens >= min_tokens:
            # 충분히 긴 노드는 독립 청크
            if current_group:
                groups.append(current_group)
            groups.append([node])
            current_group = []
            current_tokens = 0
        else:
            # 짧은 노드는 현재 그룹에 추가
            current_group.append(node)
            current_tokens += node_tokens

    if current_group:
        groups.append(current_group)

    return groups


@dataclass
class DocumentMetadata:
    """PDF 문서의 메타데이터."""

    insurance_company: str
    product_type: str = "실손의료보험"
    document_type: str = "보통약관"
    source_file: str = ""


def create_chunks(
    nodes: list[StructureNode],
    doc_meta: DocumentMetadata,
) -> list[Chunk]:
    """StructureNode 리스트를 Chunk 리스트로 변환한다.

    - 짧은 조항은 인접 조항과 병합
    - 긴 조항은 항(Paragraph) 단위로 분할
    - 각 청크에 메타데이터 부착
    """
    chunks: list[Chunk] = []

    # 조(Article)와 별표(Appendix)를 분리
    articles = [n for n in nodes if n.node_type == NodeType.ARTICLE]
    appendices = [n for n in nodes if n.node_type == NodeType.APPENDIX]

    # 조항 처리: 짧은 것은 병합
    article_groups = merge_short_nodes(articles, settings.chunk_min_tokens)

    for group in article_groups:
        if len(group) == 1:
            node = group[0]
            tokens = estimate_tokens(node.text)

            if tokens > settings.chunk_max_tokens:
                # 긴 조항 분할
                split_parts = split_long_article(node, settings.chunk_max_tokens)
                for suffix, text in split_parts:
                    if not text.strip():
                        continue
                    part_label = get_part_label(node) or ""
                    chunk_id = generate_chunk_id(doc_meta.source_file, node.number, suffix)

                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        text=text,
                        token_count=estimate_tokens(text),
                        insurance_company=doc_meta.insurance_company,
                        product_type=doc_meta.product_type,
                        document_type=doc_meta.document_type,
                        source_file=doc_meta.source_file,
                        node_type=node.node_type.value,
                        part=part_label,
                        number=node.number,
                        title=node.title,
                        hierarchy_path=_build_hierarchy(doc_meta.document_type, part_label, node.number, suffix),
                        references_to=node.references_to,
                    ))
            else:
                # 적정 크기 조항
                part_label = get_part_label(node) or ""
                chunk_id = generate_chunk_id(doc_meta.source_file, node.number)

                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    text=node.text,
                    token_count=tokens,
                    insurance_company=doc_meta.insurance_company,
                    product_type=doc_meta.product_type,
                    document_type=doc_meta.document_type,
                    source_file=doc_meta.source_file,
                    node_type=node.node_type.value,
                    part=part_label,
                    number=node.number,
                    title=node.title,
                    hierarchy_path=_build_hierarchy(doc_meta.document_type, part_label, node.number),
                    references_to=node.references_to,
                ))
        else:
            # 병합된 그룹
            merged_text = "\n\n".join(n.text for n in group)
            first_node = group[0]
            last_node = group[-1]
            all_refs = []
            for n in group:
                all_refs.extend(n.references_to)
            all_refs = list(dict.fromkeys(all_refs))  # 중복 제거, 순서 유지

            part_label = get_part_label(first_node) or ""
            number_range = f"{first_node.number}~{last_node.number}"
            chunk_id = generate_chunk_id(doc_meta.source_file, first_node.number, "merged")

            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=merged_text,
                token_count=estimate_tokens(merged_text),
                insurance_company=doc_meta.insurance_company,
                product_type=doc_meta.product_type,
                document_type=doc_meta.document_type,
                source_file=doc_meta.source_file,
                node_type="article_merged",
                part=part_label,
                number=number_range,
                title=f"{first_node.title} ~ {last_node.title}".strip(" ~"),
                hierarchy_path=_build_hierarchy(doc_meta.document_type, part_label, number_range),
                references_to=all_refs,
            ))

    # 별표 처리
    for node in appendices:
        chunk_id = generate_chunk_id(doc_meta.source_file, node.number)
        chunks.append(Chunk(
            chunk_id=chunk_id,
            text=node.text,
            token_count=estimate_tokens(node.text),
            insurance_company=doc_meta.insurance_company,
            product_type=doc_meta.product_type,
            document_type=doc_meta.document_type,
            source_file=doc_meta.source_file,
            node_type=node.node_type.value,
            part="",
            number=node.number,
            title=node.title,
            hierarchy_path=f"{doc_meta.document_type} > {node.number}",
            references_to=node.references_to,
        ))

    logger.info(
        "청킹 완료: %d개 청크 (평균 %d 토큰)",
        len(chunks),
        sum(c.token_count for c in chunks) // max(len(chunks), 1),
    )

    return chunks


def _build_hierarchy(doc_type: str, part: str, number: str, suffix: str = "") -> str:
    """계층 경로 문자열을 생성한다."""
    parts = [doc_type]
    if part:
        parts.append(part)
    parts.append(number)
    if suffix:
        parts.append(suffix)
    return " > ".join(parts)


def save_chunks(chunks: list[Chunk], output_dir: str | Path) -> Path:
    """청크를 JSON 파일로 저장한다."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not chunks:
        logger.warning("저장할 청크가 없습니다.")
        return output_dir

    source_file = chunks[0].source_file
    stem = Path(source_file).stem
    output_path = output_dir / f"{stem}_chunks.json"

    data = [chunk.to_dict() for chunk in chunks]
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("청크 저장: %s (%d개)", output_path, len(chunks))
    return output_path


def print_chunk_stats(chunks: list[Chunk]) -> None:
    """청크 통계를 출력한다."""
    if not chunks:
        print("청크가 없습니다.")
        return

    token_counts = [c.token_count for c in chunks]
    total = len(chunks)
    avg = sum(token_counts) // total
    min_t = min(token_counts)
    max_t = max(token_counts)

    in_range = sum(
        1
        for t in token_counts
        if settings.chunk_min_tokens <= t <= settings.chunk_max_tokens
    )

    types = {}
    for c in chunks:
        types[c.node_type] = types.get(c.node_type, 0) + 1

    print(f"\n{'='*50}")
    print(f"청크 통계")
    print(f"{'='*50}")
    print(f"총 청크 수: {total}")
    print(f"토큰 수 - 평균: {avg}, 최소: {min_t}, 최대: {max_t}")
    print(f"적정 범위({settings.chunk_min_tokens}~{settings.chunk_max_tokens}) 비율: {in_range}/{total} ({in_range/total*100:.1f}%)")
    print(f"노드 유형별: {types}")
    print(f"{'='*50}\n")
