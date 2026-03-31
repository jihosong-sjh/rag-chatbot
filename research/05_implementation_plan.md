# 보험약관 RAG 챗봇 POC 구현계획

> 작성일: 2026-03-31
> 프로젝트: 보험 RAG 챗봇
> 기반: 01~04 리서치 결과 종합

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [프로젝트 구조](#2-프로젝트-구조)
3. [Phase 1: 데이터 확보 + PDF 파싱](#3-phase-1-데이터-확보--pdf-파싱)
4. [Phase 2: 임베딩 + 벡터 DB + 검색](#4-phase-2-임베딩--벡터-db--검색)
5. [Phase 3: RAG 파이프라인 + 답변 생성](#5-phase-3-rag-파이프라인--답변-생성)
6. [Phase 4: 평가 + 품질 검증](#6-phase-4-평가--품질-검증)
7. [기술 스택](#7-기술-스택)
8. [의존성 목록](#8-의존성-목록)
9. [타임라인](#9-타임라인)
10. [POC 이후 확장 방향](#10-poc-이후-확장-방향)

---

## 1. 프로젝트 개요

### 배경

공개된 보험약관 PDF를 기반으로 고객 질문에 답변하는 RAG 챗봇을 만드는 사이드 프로젝트이다. 추후 실제 서비스 출시를 목표로 하며, POC를 통해 기술적 가능성을 먼저 검증한다.

### 합의된 제약 조건

| 항목 | 결정 사항 |
|------|-----------|
| **인프라** | 로컬 개발 → 추후 클라우드 배포 |
| **LLM** | Ollama 로컬 모델 (비용 최소화), 품질 검증 시에만 Claude API |
| **데이터** | 실손의료보험 1종류, 손보사 3~5개 약관 수동 다운로드 |
| **기술 스택** | 검증에 좋은 것 위주 (리서치 결과 기반) |

### 성공 기준

**최소 성공 (이 방향 계속 진행 가능)**
- 약관 PDF에서 텍스트 추출 → 조항 단위 청킹이 정상 동작
- "입원 시 보험금은 얼마인가?" 류의 단순 질문에 정확한 조항을 찾아서 답변
- 답변에 출처(몇 조 몇 항)가 포함됨

**기대 성공 (서비스로 발전 가치 있음)**
- "도수치료는 실손보험에서 보장되는가?" 같은 실생활 질문에 정확히 답변
- 약관에 없는 내용에 대해 "해당 내용은 약관에서 확인되지 않습니다" 라고 거절
- 여러 보험사 약관을 구분해서 답변 가능

---

## 2. 프로젝트 구조

```
rag-chatbot/
├── research/                          # [기존] 리서치 문서
│   ├── 01_data_sources.md
│   ├── 02_pdf_quality_analysis.md
│   ├── 03_similar_projects.md
│   ├── 04_papers_and_architecture.md
│   └── 05_implementation_plan.md      # 본 문서
│
├── data/
│   ├── raw/                           # 원본 PDF 저장
│   │   ├── standard/                  # 금감원 표준약관
│   │   └── companies/                 # 보험사별 약관
│   │       ├── samsung_fire/
│   │       ├── hyundai_marine/
│   │       ├── db_insurance/
│   │       ├── kb_insurance/
│   │       └── meritz_fire/
│   ├── parsed/                        # 파싱된 마크다운
│   └── chunks/                        # 청킹된 결과물 (JSON)
│
├── src/
│   ├── __init__.py
│   ├── config.py                      # 전역 설정 (모델명, 경로, 파라미터)
│   │
│   ├── parsing/                       # Phase 1: PDF 파싱
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py           # pymupdf4llm 기반 텍스트 추출
│   │   ├── table_extractor.py         # pdfplumber 기반 표 추출
│   │   ├── structure_parser.py        # 약관 계층 구조 파서 (관/조/항/호)
│   │   └── chunker.py                 # 구조 기반 청킹 엔진
│   │
│   ├── indexing/                      # Phase 2: 임베딩 + 인덱싱
│   │   ├── __init__.py
│   │   ├── embedder.py                # KURE-v1 임베딩
│   │   ├── bm25_indexer.py            # BM25 희소 인덱스
│   │   └── vector_store.py            # ChromaDB 벡터 저장소
│   │
│   ├── retrieval/                     # Phase 2-3: 검색
│   │   ├── __init__.py
│   │   ├── hybrid_retriever.py        # 하이브리드 검색 (BM25 + Dense + RRF)
│   │   └── reranker.py                # Cross-Encoder 리랭킹
│   │
│   ├── generation/                    # Phase 3: 답변 생성
│   │   ├── __init__.py
│   │   ├── prompt_templates.py        # 프롬프트 템플릿
│   │   ├── llm_client.py             # Ollama/Claude LLM 클라이언트
│   │   └── rag_chain.py              # RAG 파이프라인 오케스트레이션
│   │
│   └── evaluation/                    # Phase 4: 평가
│       ├── __init__.py
│       ├── dataset_builder.py         # 평가 데이터셋 생성
│       ├── ragas_evaluator.py         # RAGAS 기반 평가
│       └── domain_evaluator.py        # 보험 도메인 맞춤 평가
│
├── scripts/
│   ├── 01_parse_pdfs.py               # PDF 파싱 실행 스크립트
│   ├── 02_build_index.py              # 인덱스 구축 스크립트
│   ├── 03_run_rag.py                  # RAG 파이프라인 실행 (CLI)
│   └── 04_evaluate.py                 # 평가 실행 스크립트
│
├── notebooks/
│   ├── 01_pdf_parsing_exploration.ipynb
│   ├── 02_embedding_experiments.ipynb
│   ├── 03_retrieval_tuning.ipynb
│   └── 04_evaluation_analysis.ipynb
│
├── tests/
│   ├── test_pdf_extractor.py
│   ├── test_structure_parser.py
│   ├── test_chunker.py
│   ├── test_retrieval.py
│   └── test_rag_chain.py
│
├── eval_data/
│   ├── qa_pairs.json                  # 평가용 QA 쌍
│   └── edge_cases.json                # 엣지 케이스 (거절 답변 등)
│
├── pyproject.toml                     # 의존성 관리 (uv)
├── Makefile                           # 자주 쓰는 명령어 단축
├── .env.example                       # 환경 변수 템플릿
├── .gitignore
└── README.md
```

### 설계 원칙

- `src/` 내부를 파이프라인 단계별로 분리하여, 각 Phase를 독립적으로 개발·테스트
- `scripts/`에 단계별 실행 진입점을 두어, 각 Phase의 산출물을 순차적으로 생성
- `notebooks/`에서 탐색적 실험 → 검증된 코드를 `src/`로 이동
- `data/`는 `.gitignore`에 포함, 디렉토리 구조만 유지 (`.gitkeep`)

---

## 3. Phase 1: 데이터 확보 + PDF 파싱

> 예상 소요: 1~1.5주 (사이드 프로젝트 기준)

### 목표

실손의료보험 약관 PDF에서 텍스트를 추출하고, 약관의 계층 구조(관/조/항/호)를 보존한 채로 청킹하여 JSON 형태로 저장한다.

### 산출물

- `data/raw/` 에 보험사별 실손의료보험 약관 PDF 5건 + 표준약관 1건
- `data/parsed/` 에 Markdown으로 변환된 텍스트
- `data/chunks/` 에 메타데이터가 부착된 청크 JSON 파일

### 세부 작업

#### 3-1. 데이터 수동 다운로드 (1일)

- **소스**: 손해보험협회 공시실 (kpub.knia.or.kr)
- **대상 보험사**: 삼성화재, 현대해상, DB손해보험, KB손해보험, 메리츠화재
- **추가**: 금감원 실손의료보험 표준약관 1건
- **파일명 규칙**: `{보험사코드}_{상품명}_{시행일}.pdf`
  - 예: `samsung_fire_silson_2025.pdf`

#### 3-2. PDF 텍스트 추출기 (`pdf_extractor.py`) (2일)

- pymupdf4llm으로 PDF → Markdown 변환
- PDF 유형 자동 감지 (페이지당 추출 텍스트 길이로 텍스트/스캔 판별)
- pdfplumber로 pymupdf4llm이 놓친 표를 보완 추출

#### 3-3. 약관 구조 파서 (`structure_parser.py`) (3일) ← Phase 1의 핵심

정규표현식 기반 약관 계층 구조 파싱:

```
관(Part):          "제N관", "제N편"
조(Article):       "제N조", "제N조의N"
항(Paragraph):     "①", "②" 또는 "(1)", "(2)"
호(Subparagraph):  "1.", "2." 또는 "가.", "나."
별표:              "【별표N】", "[별표 N]"
```

상호 참조 감지: "제N조에 따라", "별표N에서 정한" 등의 패턴을 정규표현식으로 추출하여 `references_to` 메타데이터 생성

#### 3-4. 구조 기반 청커 (`chunker.py`) (2일)

- **기본 청크 단위**: 조(Article)
- **청크 크기**: 800~1,500 토큰 (한국어 정보 밀도 고려)
- **짧은 조항** (< 300 토큰): 인접 조항과 병합
- **긴 조항** (> 1,500 토큰): 항(Paragraph) 단위로 분할, 조항 제목을 각 청크 앞에 반복 삽입
- **별표/부표**: 독립 청크로 분리, 본문 조항과의 연결 메타데이터 보존

청크 메타데이터 스키마:

```json
{
  "chunk_id": "samsung_fire_silson_2025_art10_p2",
  "insurance_company": "삼성화재",
  "product_type": "실손의료보험",
  "document_type": "보통약관",
  "part": "제2관 보험금의 지급",
  "article": "제10조",
  "article_title": "보험금의 종류와 지급사유",
  "paragraph": "제2항",
  "hierarchy_path": "보통약관 > 제2관 > 제10조 > 제2항",
  "page_number": 15,
  "references_to": ["제2조", "별표1"],
  "source_file": "samsung_fire_silson_2025.pdf"
}
```

### Phase 1 검증

| 검증 항목 | 방법 | 성공 기준 |
|-----------|------|-----------|
| 텍스트 추출 정확도 | 원본 3개 조항 수동 비교 | 일치율 95% 이상 |
| 구조 파싱 정확도 | 파싱 결과 vs PDF 목차 비교 | 조항 감지율 90% 이상 |
| 청크 품질 | 토큰 수 분포 통계 | 800~1500 범위 내 비율 80% 이상 |

---

## 4. Phase 2: 임베딩 + 벡터 DB + 검색

> 예상 소요: 1~1.5주

### 목표

청크를 임베딩하여 ChromaDB에 저장하고, 하이브리드 검색(BM25 + Dense + RRF)을 구현한다.

### 산출물

- ChromaDB 컬렉션 (임베딩 + 메타데이터)
- BM25 인덱스
- 하이브리드 검색 API (`query → top-k chunks`)

### 세부 작업

#### 4-1. 임베딩 파이프라인 (`embedder.py`) (2일)

- **1순위 모델**: `nlpai-lab/KURE-v1`
  - 1024차원, 최대 8192 토큰, 0.6B 파라미터
  - 한국어 검색 벤치마크 1위 (Recall@1: 0.5264)
  - MIT 라이선스
- **대안**: `BAAI/bge-m3` (KURE-v1 로딩 문제 시)
- HuggingFace `sentence-transformers` 라이브러리로 로드
- 배치 임베딩 + chunk_id 기반 캐싱

#### 4-2. 벡터 저장소 (`vector_store.py`) (1일)

- ChromaDB persistent 저장 (`data/chromadb/`)
- 단일 컬렉션 `insurance_clauses`, 메타데이터 필터링으로 보험사/상품 구분
- CRUD: add_chunks, search, delete_by_source

#### 4-3. BM25 인덱스 (`bm25_indexer.py`) (1일)

- `rank_bm25` 라이브러리
- `kiwipiepy` (Kiwi)로 한국어 형태소 분석 기반 토큰화
  - mecab-ko 대비 설치 간편, 사용자 사전 추가 용이
- 보험 도메인 사용자 사전 기초 구축 (50~100개 용어)
- pickle 직렬화 저장

#### 4-4. 하이브리드 검색 (`hybrid_retriever.py`) (2일)

```
BM25 top-20
              → RRF 통합 → top-10
Dense top-20

RRF 공식: score(d) = Σ 1/(k + rank(d)), k=60
```

- 메타데이터 필터 지원 (보험사별, 약관 유형별)

#### 4-5. 리랭커 (`reranker.py`) (1일) - 선택적

- `BAAI/bge-reranker-v2-m3` (다국어 Cross-Encoder)
- 하이브리드 top-10 → 리랭킹 → top-5
- on/off 가능하게 구현

### Phase 2 검증

| 검증 항목 | 방법 | 성공 기준 |
|-----------|------|-----------|
| 검색 정확도 | 수동 질의 10건 Precision@5 | >= 0.6 |
| 하이브리드 효과 | BM25 vs Dense vs Hybrid 비교 | Hybrid가 단독 대비 개선 |

---

## 5. Phase 3: RAG 파이프라인 + 답변 생성

> 예상 소요: 1~1.5주

### 목표

검색된 컨텍스트를 LLM에 전달하여, 출처(조항 번호)가 포함된 정확한 답변을 생성한다.

### Ollama 로컬 모델 선정

| 모델 | 크기 | 한국어 성능 | VRAM | 권장 |
|------|------|-------------|------|------|
| **EXAONE-3.5:7.8b** | 7.8B | 매우 우수 (LG AI Research, 한국어 특화) | ~6GB | **1순위** |
| Qwen2.5:7b | 7B | 우수 (CJK 강점) | ~5GB | 2순위 |
| gemma3:12b | 12B | 양호 | ~8GB | 메모리 여유 시 |

EXAONE-3.5 선정 이유: LG AI Research가 개발한 모델로, 한국어 이해와 생성에서 동급 크기 모델 중 최고 수준. 7.8B는 일반 개발 노트북(16GB+ RAM)에서 구동 가능.

### 세부 작업

#### 5-1. LLM 클라이언트 (`llm_client.py`) (1일)

- Ollama: `http://localhost:11434/api/chat`
- Claude: `anthropic.Anthropic()` (환경 변수 `ANTHROPIC_API_KEY`)
- 공통 인터페이스: `generate(prompt, system_prompt, temperature, max_tokens) → str`
- temperature: 0.0~0.1 (사실 기반 답변)

#### 5-2. 프롬프트 엔지니어링 (`prompt_templates.py`) (1.5일) ← Phase 3 핵심

**시스템 프롬프트**:

```
당신은 보험약관 전문 상담 AI입니다. 아래 규칙을 반드시 따르세요:

1. 제공된 약관 내용만을 근거로 답변하세요.
2. 답변에는 반드시 근거가 되는 약관 조항 번호(예: 제10조 제2항)를 명시하세요.
3. 제공된 약관에서 확인할 수 없는 내용에 대해서는
   "해당 약관에서 확인되지 않는 내용입니다. 보험사 고객센터에 문의하시기 바랍니다."
   라고 답변하세요.
4. 보험 상품 추천, 가입 권유는 하지 마세요.
5. 답변은 일반인이 이해할 수 있는 쉬운 표현으로 작성하되,
   핵심 법률 용어는 괄호 안에 원문을 병기하세요.
```

**사용자 프롬프트 템플릿**:

```
[참조 약관]
{검색된 청크들 - 출처 메타데이터 포함}

[질문]
{사용자 질문}

위 약관 내용을 바탕으로 질문에 답변해주세요.
```

#### 5-3. RAG 체인 (`rag_chain.py`) (2일)

```
사용자 질문 → 하이브리드 검색 → (리랭킹) → 컨텍스트 구성 → LLM 생성 → 답변
```

- 검색된 top-5 청크를 `[출처: {보험사} {약관유형} {조항번호}]` 태그와 함께 포맷
- 유사도 임계값 미만 시 LLM 미호출, 직접 거절 응답 반환

#### 5-4. CLI 인터페이스 (`scripts/03_run_rag.py`) (0.5일)

- 대화형 모드
- `--model ollama|claude` 모델 전환
- `--verbose` 검색 결과 상세 출력

### Phase 3 검증

| 검증 항목 | 테스트 질문 | 성공 기준 |
|-----------|-------------|-----------|
| 단순 질문 | "보험금 청구 시 필요한 서류는?", "면책 사유는?" 등 5개 | 5/5 정확한 조항 인용 |
| 실생활 질문 | "도수치료 보장 여부", "MRI 비용 보장" 등 5개 | 4/5 이상 적절 |
| 거절 답변 | "성형수술 보험 처리?" | 정상 거절 |
| 모델 비교 | 동일 10개 질문 Ollama vs Claude | 정성 비교 리포트 |

---

## 6. Phase 4: 평가 + 품질 검증

> 예상 소요: 1주

### 목표

체계적인 평가 체계를 구축하여 검색 품질과 생성 품질을 정량적으로 측정한다.

### 세부 작업

#### 6-1. 평가 데이터셋 구축 (2일)

총 70개 이상:
- 단순 사실 질문: 30개 (조항 위치, 정의)
- 실생활 매핑 질문: 15개 (일상 표현 → 약관)
- 거절 질문: 10개 (약관 외, 상품 추천 등)
- 다중 조항 참조: 5개 (여러 조항 종합 필요)
- 엣지 케이스: 10개 (모호한 질문 등)

각 QA 쌍 형식:

```json
{
  "question": "도수치료를 받으면 실손보험에서 보장이 되나요?",
  "ground_truth_answer": "제N조에 따라 ...",
  "relevant_chunks": ["samsung_fire_silson_2025_art10_p2"],
  "answer_type": "factual",
  "difficulty": "medium"
}
```

#### 6-2. RAGAS 평가 (2일)

- RAGAS 프레임워크 연동
- RAGAS의 LLM-as-Judge에 Claude API 사용

측정 지표:
- **Faithfulness**: 답변이 검색된 컨텍스트에 기반하는 정도
- **Answer Relevancy**: 답변이 질문에 적절한 정도
- **Context Precision**: 관련 컨텍스트가 상위에 위치하는 정도
- **Context Recall**: 필요한 컨텍스트가 검색된 정도

#### 6-3. 보험 도메인 맞춤 평가 (1일)

- **조항 정확성 (Clause Accuracy)**: 인용 조항이 실제 존재하며 내용 정확한지
- **출처 추적성 (Traceability)**: 답변에 조항 번호가 명시되었는지
- **거절 적절성 (Refusal Quality)**: 약관 외 질문에 올바르게 거절했는지

#### 6-4. 결과 분석 (2일)

- 지표별 점수 분포 시각화
- 오답 분류: 검색 실패 vs 생성 실패
- 보험사별/질문 유형별 성능 차이 분석
- 개선 우선순위 도출

### Phase 4 목표치

| 지표 | POC 목표 |
|------|----------|
| RAGAS Faithfulness | >= 0.7 |
| RAGAS Answer Relevancy | >= 0.7 |
| RAGAS Context Precision | >= 0.6 |
| RAGAS Context Recall | >= 0.6 |
| 조항 정확성 | >= 80% |
| 거절 적절성 | >= 80% |

---

## 7. 기술 스택

| 컴포넌트 | 선택 | 선택 이유 |
|----------|------|-----------|
| **언어** | Python 3.11+ | RAG 생태계 표준 |
| **패키지 관리** | uv | pip 대비 10-100배 빠른 설치, lockfile 지원 |
| **PDF 파싱 (1순위)** | pymupdf4llm | PDF→Markdown 변환 특화, 처리 속도 매우 빠름 |
| **PDF 표 추출 (보완)** | pdfplumber | CJK 지원 우수, 표 추출 정확도 96%+ |
| **형태소 분석** | kiwipiepy | 설치 간편, 사용자 사전 용이, 외부 의존성 없음 |
| **임베딩** | KURE-v1 | 한국어 검색 1위, 8192 토큰, MIT 라이선스 |
| **벡터 DB** | ChromaDB | 로컬 실행, 간편, 메타데이터 필터링 |
| **BM25** | rank_bm25 | 경량 Python 구현, 커스텀 토크나이저 연동 |
| **리랭커** | bge-reranker-v2-m3 | 다국어 Cross-Encoder, BGE 계열 호환 |
| **LLM (메인)** | Ollama + EXAONE-3.5:7.8b | 비용 제로, 한국어 최고 수준 (7B급) |
| **LLM (검증)** | Claude API | 품질 상한선 확인, RAGAS Judge |
| **오케스트레이션** | 직접 구현 | POC에서 디버깅 용이, 블랙박스 방지 |
| **평가** | RAGAS + 커스텀 | 표준 + 도메인 특화 |
| **노트북** | Jupyter Lab | 탐색적 실험, 시각화 |

### LangChain 미사용 결정

POC에서 중요한 것은 (1) 각 컴포넌트 동작 원리의 정확한 이해, (2) 디버깅 용이성이다. LangChain의 추상화는 프로덕션에서는 생산성을 높이지만, POC에서는 블랙박스가 되어 문제 진단을 어렵게 할 수 있다. 대신 각 모듈을 명확한 인터페이스로 분리하여, 추후 LangChain/LangGraph 전환 비용을 최소화한다.

---

## 8. 의존성 목록

```toml
[project]
name = "insurance-rag-chatbot"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # PDF 파싱
    "pymupdf4llm>=0.0.17",
    "pymupdf>=1.25.0",
    "pdfplumber>=0.11.0",

    # 한국어 NLP
    "kiwipiepy>=0.21.0",

    # 임베딩 & 벡터 DB
    "sentence-transformers>=3.4.0",
    "chromadb>=0.6.0",
    "rank-bm25>=0.2.2",

    # LLM
    "httpx>=0.28.0",               # Ollama REST API
    "anthropic>=0.42.0",           # Claude API (검증용)

    # 평가
    "ragas>=0.2.0",

    # 유틸리티
    "pydantic>=2.10.0",
    "python-dotenv>=1.0.0",
    "tqdm>=4.67.0",
    "rich>=13.9.0",
]

[project.optional-dependencies]
dev = [
    "jupyterlab>=4.3.0",
    "pytest>=8.3.0",
    "matplotlib>=3.10.0",
    "seaborn>=0.13.0",
]

reranker = [
    "transformers>=4.47.0",
    "torch>=2.5.0",
]
```

### 설계 원칙

- `reranker`를 optional dependency로 분리: PyTorch가 무거우므로, 리랭킹 없이도 기본 파이프라인 동작
- Ollama 통신은 `httpx`만으로 충분 (별도 SDK 불필요)

---

## 9. 타임라인

```
Week 1:  Phase 1 - 데이터 확보 + PDF 파싱 파이프라인
Week 2:  Phase 2 - 임베딩 + 벡터 DB + 검색 파이프라인
Week 3:  Phase 3 - RAG 파이프라인 + 답변 생성
Week 4:  Phase 4 - 평가 + 품질 검증 + 개선점 정리
```

풀타임 기준 4주. 사이드 프로젝트 투자 시간에 따라 6~8주 소요 가능. 각 Phase는 이전 Phase 산출물에 의존하므로 순차 진행.

---

## 10. POC 이후 확장 방향

| 항목 | POC에서 안 하는 이유 | 확장 시점 |
|------|---------------------|-----------|
| 웹 UI (FastAPI + React) | 파이프라인 품질 검증이 우선 | POC 통과 후 즉시 |
| LangGraph 에이전트 | 단순 파이프라인으로 기본 품질 확보 | 복잡 질의 처리 필요 시 |
| 임베딩 파인튜닝 | 기본 KURE-v1 성능으로 충분 | 검색 품질 병목 확인 시 |
| 자동 크롤러 | 5건은 수동 다운로드 | 다품종 확장 시 |
| Docker 배포 | 로컬 개발 우선 | 팀 협업 또는 배포 시 |
| 약관 비교 기능 | 단일 상품 품질 확보 우선 | 다사 약관 인덱싱 완료 후 |

---

## Phase별 검증 요약

| Phase | 검증 항목 | 성공 기준 |
|-------|-----------|-----------|
| 1 | 텍스트 추출 정확도 | 일치율 95% |
| 1 | 구조 파싱 정확도 | 감지율 90% |
| 1 | 청크 토큰 분포 | 800~1500 범위 80% |
| 2 | 검색 Precision@5 | >= 0.6 |
| 2 | 하이브리드 검색 효과 | Hybrid > 단독 |
| 3 | 단순 질문 조항 인용 | 5/5 |
| 3 | 실생활 질문 적절성 | 4/5+ |
| 3 | 거절 답변 | 정상 거절 |
| 4 | RAGAS Faithfulness | >= 0.7 |
| 4 | RAGAS Answer Relevancy | >= 0.7 |
| 4 | 조항 정확성 | >= 80% |
| 4 | 거절 적절성 | >= 80% |
