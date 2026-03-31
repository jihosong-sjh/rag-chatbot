"""보험약관 계층 구조 파서.

정규표현식을 사용하여 약관 텍스트에서
관(Part)/조(Article)/항(Paragraph)/호(Subparagraph)/별표(Appendix)
구조를 파싱하고, 조항 간 상호 참조 관계를 추출한다.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """약관 구조 노드 유형."""

    DOCUMENT = "document"
    PART = "part"          # 관/편
    ARTICLE = "article"    # 조
    PARAGRAPH = "paragraph"  # 항
    SUBPARAGRAPH = "subparagraph"  # 호
    APPENDIX = "appendix"  # 별표/부표


@dataclass
class StructureNode:
    """약관 구조 트리의 노드."""

    node_type: NodeType
    number: str  # "제1관", "제10조", "①" 등
    title: str  # "(보험금의 지급사유)" 등
    text: str  # 해당 노드의 본문 텍스트
    page_number: int | None = None
    children: list[StructureNode] = field(default_factory=list)
    references_to: list[str] = field(default_factory=list)

    @property
    def full_label(self) -> str:
        """번호 + 제목 형태의 전체 레이블."""
        if self.title:
            return f"{self.number} {self.title}"
        return self.number

    @property
    def hierarchy_path(self) -> str:
        """계층 경로는 청커에서 부모 정보를 조합하여 생성."""
        return self.full_label


# ── 정규표현식 패턴 ──

# 관/편: "제1관", "제2편", "제1관 총칙" 등
PART_PATTERN = re.compile(
    r"^[#\s]*(?P<number>제\s*\d+\s*[관편])\s*(?P<title>[^\n]*)",
    re.MULTILINE,
)

# 조: "제1조", "제10조의2", "제10조(보험금의 지급사유)" 등
ARTICLE_PATTERN = re.compile(
    r"^[#\s]*(?P<number>제\s*\d+(?:조의\d+|조))\s*(?P<title>\([^)]*\))?\s*(?P<rest>[^\n]*)",
    re.MULTILINE,
)

# 조 (대안 패턴): "## 3. (보장종목별 보상내용)" 등 숫자. 형식 (DB손보 등)
ARTICLE_NUMBERED_PATTERN = re.compile(
    r"^[#\s]*(?P<number>\d+)\.\s*(?P<title>\([^)]*\))\s*(?P<rest>[^\n]*)",
    re.MULTILINE,
)

# 항: ①, ②, ③ 등 (원 숫자) 또는 ⑴, ⑵ 또는 괄호 숫자
PARAGRAPH_PATTERN = re.compile(
    r"^(?P<number>[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(?P<text>[^\n]*)",
    re.MULTILINE,
)

# 호: "1.", "2.", "가.", "나." 등 (줄 시작)
SUBPARAGRAPH_PATTERN = re.compile(
    r"^\s+(?P<number>\d+\.|[가-하]\.)\s*(?P<text>[^\n]*)",
    re.MULTILINE,
)

# 별표/부표: 【별표1】, [별표 1], 〈별표1〉 등
APPENDIX_PATTERN = re.compile(
    r"^[#\s]*(?P<number>[【\[〈<]?\s*별표\s*\d+\s*[】\]〉>]?)\s*(?P<title>[^\n]*)",
    re.MULTILINE,
)

# ── 상호 참조 패턴 ──

# "제N조", "제N조의N", "제N조 제N항" 참조
ARTICLE_REF_PATTERN = re.compile(r"제\s*(\d+)\s*(?:조의\s*\d+|조)(?:\s*제\s*(\d+)\s*항)?")

# 별표 참조: "별표 1", "【별표1】" 등
APPENDIX_REF_PATTERN = re.compile(r"별표\s*(\d+)")

# 외부 법률 참조: 「상법」, 「보험업법」 등
EXTERNAL_LAW_PATTERN = re.compile(r"[「『]([^」』]+)[」』]")


def extract_references(text: str) -> list[str]:
    """텍스트에서 상호 참조를 추출한다.

    Returns:
        참조 대상 목록. 예: ["제2조", "제15조 제3항", "별표1", "상법"]
    """
    refs: list[str] = []

    for match in ARTICLE_REF_PATTERN.finditer(text):
        article_num = match.group(1)
        paragraph_num = match.group(2)
        if paragraph_num:
            refs.append(f"제{article_num}조 제{paragraph_num}항")
        else:
            refs.append(f"제{article_num}조")

    for match in APPENDIX_REF_PATTERN.finditer(text):
        refs.append(f"별표{match.group(1)}")

    for match in EXTERNAL_LAW_PATTERN.finditer(text):
        refs.append(match.group(1))

    # 중복 제거 (순서 유지)
    seen: set[str] = set()
    unique_refs: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)

    return unique_refs


def parse_articles(markdown_text: str) -> list[StructureNode]:
    """Markdown 텍스트에서 조(Article) 단위 구조를 파싱한다.

    이 함수는 약관 텍스트를 조(Article) 단위로 분할하여
    StructureNode 리스트를 반환한다. 각 노드에는 해당 조의
    본문 텍스트와 상호 참조 정보가 포함된다.

    Returns:
        조(Article) 단위 StructureNode 리스트.
    """
    nodes: list[StructureNode] = []

    # 조(Article) 위치를 모두 찾기 (기본 패턴)
    article_matches = list(ARTICLE_PATTERN.finditer(markdown_text))
    use_numbered = False

    if not article_matches:
        # 대안 패턴 시도: "## 3. (보장종목별 보상내용)" 형식
        article_matches = list(ARTICLE_NUMBERED_PATTERN.finditer(markdown_text))
        use_numbered = True

    if not article_matches:
        logger.warning("약관에서 조(Article) 패턴을 찾을 수 없습니다.")
        return nodes

    logger.info("조(Article) %d개 감지됨 (numbered=%s)", len(article_matches), use_numbered)

    for i, match in enumerate(article_matches):
        raw_number = match.group("number").replace(" ", "")
        number = f"제{raw_number}조" if use_numbered else raw_number
        title = match.group("title") or ""
        title = title.strip()

        # 이 조의 본문: 현재 조 시작 ~ 다음 조 시작 (또는 문서 끝)
        start = match.start()
        end = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(markdown_text)
        article_text = markdown_text[start:end].strip()

        # 상호 참조 추출 (자기 자신 제외)
        refs = extract_references(article_text)
        self_ref = number.replace(" ", "")
        refs = [r for r in refs if not r.startswith(self_ref)]

        node = StructureNode(
            node_type=NodeType.ARTICLE,
            number=number,
            title=title,
            text=article_text,
            references_to=refs,
        )
        nodes.append(node)

    return nodes


def parse_appendices(markdown_text: str) -> list[StructureNode]:
    """Markdown 텍스트에서 별표(Appendix)를 파싱한다."""
    nodes: list[StructureNode] = []

    appendix_matches = list(APPENDIX_PATTERN.finditer(markdown_text))

    if not appendix_matches:
        return nodes

    logger.info("별표(Appendix) %d개 감지됨", len(appendix_matches))

    for i, match in enumerate(appendix_matches):
        number = match.group("number").strip()
        # 대괄호 등 정규화
        number = re.sub(r"[【】\[\]〈〉<>]", "", number).strip()
        title = match.group("title").strip()

        start = match.start()
        end = appendix_matches[i + 1].start() if i + 1 < len(appendix_matches) else len(markdown_text)
        appendix_text = markdown_text[start:end].strip()

        refs = extract_references(appendix_text)

        node = StructureNode(
            node_type=NodeType.APPENDIX,
            number=number,
            title=title,
            text=appendix_text,
            references_to=refs,
        )
        nodes.append(node)

    return nodes


def detect_current_part(text_before: str) -> str | None:
    """주어진 텍스트 위치 이전의 가장 최근 관(Part)을 찾는다."""
    matches = list(PART_PATTERN.finditer(text_before))
    if matches:
        last = matches[-1]
        number = last.group("number").replace(" ", "")
        title = last.group("title").strip()
        return f"{number} {title}".strip()
    return None


def parse_structure(markdown_text: str) -> list[StructureNode]:
    """약관 전체 구조를 파싱한다.

    조(Article)와 별표(Appendix)를 모두 파싱하여 반환한다.
    각 조에는 소속 관(Part) 정보가 hierarchy에 반영된다.

    Returns:
        StructureNode 리스트 (조 + 별표).
    """
    # 조(Article) 파싱
    articles = parse_articles(markdown_text)

    # 각 조에 소속 관(Part) 정보 추가
    for node in articles:
        # 해당 조 이전의 텍스트에서 관 정보를 탐색
        article_pos = markdown_text.find(node.text[:50]) if node.text else -1
        if article_pos > 0:
            part_label = detect_current_part(markdown_text[:article_pos])
            if part_label:
                # title에 관 정보를 포함하지 않고, 별도 속성으로 관리하기 위해
                # StructureNode에는 없으므로 text의 메타데이터로 활용
                node._part_label = part_label  # type: ignore[attr-defined]

    # 별표(Appendix) 파싱
    appendices = parse_appendices(markdown_text)

    all_nodes = articles + appendices

    logger.info(
        "구조 파싱 완료: 조 %d개, 별표 %d개",
        len(articles),
        len(appendices),
    )

    return all_nodes


def get_part_label(node: StructureNode) -> str | None:
    """노드의 소속 관(Part) 레이블을 반환한다."""
    return getattr(node, "_part_label", None)
