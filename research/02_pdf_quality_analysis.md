# 보험약관 PDF 품질 및 텍스트 추출 가능성 분석

> 작성일: 2026-03-31
> 프로젝트: 보험 RAG 챗봇
> 목적: 보험약관 PDF의 특성을 파악하고, 텍스트 추출 및 RAG 파이프라인 구축을 위한 기술적 전략을 수립하기 위한 도메인 리서치

---

## 1. 한국 보험약관 PDF의 일반적인 특성

### 1.1 텍스트 기반 PDF vs 스캔 이미지 PDF 비율

| 구분 | 비율(추정) | 비고 |
|------|-----------|------|
| 텍스트 기반 PDF | 약 85~95% | 대부분의 보험사가 디지털 방식으로 약관 생성 |
| 스캔 이미지 PDF | 약 5~15% | 오래된 약관, 일부 중소형 보험사 자료 |

- **현재 추세**: 금융감독원의 전자공시 의무화, 보험사 홈페이지를 통한 약관 PDF 다운로드 서비스 확대로 대부분의 약관이 **텍스트 기반 PDF**(디지털 네이티브)로 제공됨
- 삼성생명, 한화생명, DB손해보험, KB손해보험 등 주요 보험사는 상품 공시 페이지에서 텍스트 기반 PDF 약관을 제공
- **주의 사항**: 일부 오래된 약관(2010년 이전)이나 스캔 문서가 혼재할 수 있으므로, PDF 유형을 자동 감지하는 로직이 필요

### 1.2 일반적인 약관 문서 구조

보험약관은 보험자가 다수의 보험계약자와 동종/다수의 보험계약을 체결하기 위해 일정한 형식에 의해 미리 마련한 일반적/정형적/표준적인 계약조항이다. 일반적인 보험약관의 구조는 다음과 같다:

```
보험약관 전체 구조
├── 가이드편 (안내사항)
│   ├── 가입자 유의사항
│   ├── 주요내용 요약서
│   └── 보험용어 해설
├── 보통약관
│   ├── 제1관 총칙
│   │   ├── 제1조 (목적)
│   │   ├── 제2조 (용어의 정의)
│   │   └── ...
│   ├── 제2관 보험금의 지급
│   │   ├── 보험금 지급사유
│   │   ├── 보험금을 지급하지 않는 사유
│   │   └── ...
│   ├── 제3관 계약자의 의무
│   ├── 제4관 보험계약의 성립과 유지
│   ├── 제5관 보험료의 납입
│   └── 제6관 분쟁의 해결
├── 특별약관
│   ├── 각종 특약 조항
│   └── ...
└── 별표/부표
    ├── 【별표1】 후유장해등급별 보상금액표
    ├── 【별표2】 질병코드표
    └── ...
```

### 1.3 평균적인 페이지 수 및 파일 크기

| 보험 유형 | 평균 페이지 수 | 평균 파일 크기 |
|-----------|--------------|--------------|
| 생명보험 (종신/변액) | 80~200페이지 | 1~5MB |
| 건강/질병 보험 | 60~150페이지 | 1~3MB |
| 자동차보험 | 100~180페이지 | 2~5MB |
| 화재/재물보험 | 50~120페이지 | 1~3MB |
| 여행/단기보험 | 20~50페이지 | 0.5~1.5MB |

- 종합보험 상품의 경우 특별약관 포함 시 **200페이지 이상**에 달하기도 함
- 별표(장해분류표, 질병코드표 등)가 상당한 분량을 차지하며, 표 형태의 데이터가 많음
- 생명보험협회 및 손해보험협회에서 발행하는 표준약관은 기준이 되는 문서로, 각 보험사가 이를 기반으로 자사 약관을 구성

---

## 2. PDF 텍스트 추출 도구 및 전략

### 2.1 Python 라이브러리별 한국어 PDF 처리 성능 비교

| 라이브러리 | 한국어 지원 | 표(Table) 추출 | 속도 | 레이아웃 보존 | 비고 |
|-----------|-----------|--------------|------|-------------|------|
| **PyMuPDF (fitz)** | 우수 | 보통 (별도 설정 필요) | 매우 빠름 | 우수 | 7,031페이지 PDF를 약 5초에 처리. RAG용으로 강력 추천 |
| **pdfplumber** | 우수 (CJK 지원) | 매우 우수 | 보통 | 우수 | pdfminer 기반으로 CJK(한중일) 언어 및 세로쓰기 지원. 테이블 추출에 특화 |
| **PyPDF2/pypdf** | 보통 | 미흡 | 빠름 | 보통 | 순수 Python. 단순 텍스트 추출 및 기본 조작에 적합. 복잡한 레이아웃 처리 제한적 |
| **pdfminer.six** | 우수 (CJK 지원) | 보통 | 느림 | 매우 우수 | 레이아웃 분석 자동화. pdfplumber의 기반 엔진 |
| **pymupdf4llm** | 우수 | 우수 | 매우 빠름 | 매우 우수 | PyMuPDF 확장. **PDF를 Markdown으로 변환하여 RAG에 최적화**. LlamaIndex/LangChain 통합 지원 |

#### pymupdf4llm 상세 분석 (RAG 최적 도구)

pymupdf4llm은 PyMuPDF의 확장 패키지로, PDF를 LLM/RAG에 최적화된 형태로 변환하는 데 특화되어 있다:

- **Markdown 변환**: 텍스트와 표를 감지하여 올바른 읽기 순서로 배치한 후, GitHub 호환 Markdown으로 변환
- **헤더 감지**: 폰트 크기를 기반으로 헤더를 식별하고 적절한 `#` 태그를 부여
- **서식 보존**: 볼드, 이탤릭, 모노스페이스, 코드 블록 감지 및 포맷팅
- **OCR 통합**: 스캔 문서에 대한 OCR 지원이 내장되어, OCR 추출 페이지와 네이티브 추출 페이지가 하나의 출력으로 통합
- **pymupdf-layout 확장**: AI 기반 페이지 레이아웃 분석으로 표 인식률 대폭 향상

#### 추천 전략

```
1차 선택: pymupdf4llm → Markdown 변환 → RAG 파이프라인
2차 보완: pdfplumber → 표(Table) 정밀 추출이 필요한 경우 보완 사용
3차 대안: pdfminer.six → 레이아웃이 매우 복잡한 문서의 정밀 분석
```

### 2.2 OCR이 필요한 경우의 한국어 지원 수준

스캔 이미지 기반 PDF나 이미지가 포함된 PDF의 경우 OCR(광학 문자 인식)이 필요하다.

| OCR 도구 | 한국어 정확도 | 속도 | GPU 필요 | 특이사항 |
|----------|-------------|------|---------|---------|
| **Tesseract OCR** | 보통~낮음 | 보통 | 불필요 | 한영 혼합 시 인식률 크게 저하. kor+eng 동시 모델의 정확도가 매우 낮음 |
| **EasyOCR** | 우수 | 보통~빠름 | 선택적 (GPU 지원) | 다국어 동시 인식 가능. 한영 혼합 문서에 Tesseract 대비 월등히 우수 |
| **PaddleOCR (PP-OCRv5)** | 매우 우수 | 빠름 | 선택적 | 106개 언어 지원. 한국어 전용 모델(korean_PP-OCRv5_mobile_rec) 제공. 경량화 모델로 리소스 효율적 |
| **Surya OCR** | 매우 우수 | 빠름 | 권장 | 90개 이상 언어 지원. 레이아웃 분석, 읽기 순서 감지, 표 인식까지 통합. 벤치마크에서 97.70% 정확도로 최고 수준 |

#### OCR 도구 추천 전략

```
GPU 환경 가용 시:    Surya OCR (최고 정확도) 또는 PaddleOCR (균형)
CPU 환경만 가용 시:  PaddleOCR (경량) 또는 EasyOCR
Tesseract는 한국어 보험약관에는 비추천 (한영 혼합 시 성능 저하가 심각)
```

### 2.3 표(Table), 도표 등 구조화된 데이터 추출 방법

보험약관에서 표 데이터는 매우 중요하다 (장해등급표, 질병코드표, 보험금 산출표 등).

| 방법 | 도구 | 장점 | 단점 |
|------|------|------|------|
| **규칙 기반 추출** | pdfplumber | 테이블 구조가 명확한 경우 96% 이상의 인식률. 셀 경계선 기반 추출 | 경계선 없는 표 처리 어려움 |
| **AI 기반 추출** | pymupdf-layout, Camelot | 복잡한 레이아웃에서도 표 감지 가능 | 추가 의존성, 처리 시간 증가 |
| **트랜스포머 기반** | Table Transformer, TATR | 다양한 문서 유형에서 일관된 성능 | GPU 필요, 모델 크기 큼 |
| **하이브리드 접근** | pymupdf4llm + pdfplumber | 일반 텍스트는 pymupdf4llm, 정밀 표는 pdfplumber | 구현 복잡도 증가 |

#### 보험약관 표 추출 시 주의사항

- **장해분류표**: 복잡한 계층 구조(대분류-중분류-소분류)와 퍼센트 수치가 포함된 표
- **질병코드표**: 한국표준질병사인분류(KCD) 코드가 포함된 대규모 표
- **보험료 산출표**: 나이/성별/가입금액에 따른 다차원 표
- 표 내부의 줄바꿈, 셀 병합이 빈번하여 추출 후 후처리가 필수

---

## 3. 보험약관 특유의 텍스트 처리 난이도

### 3.1 법률 용어 및 보험 전문 용어 처리

보험약관은 법률 문서의 특성과 금융 전문 용어가 결합된 독특한 텍스트 특성을 가진다.

#### 주요 난이도 요소

| 유형 | 예시 | 난이도 |
|------|------|--------|
| **법률 용어** | "고지의무", "면책사유", "소급적용", "부당이득반환" | 높음 |
| **보험 전문 용어** | "보험가액", "재조달가액", "비례보상", "실손보상", "기왕증" | 높음 |
| **복합 조건문** | "다만, 제○조에 해당하는 경우를 제외하고..." | 매우 높음 |
| **숫자/비율 표현** | "보험가입금액의 80%에 해당하는 금액" | 보통 |
| **한자 혼용** | "免責(면책)", "被保險者(피보험자)" | 보통 |
| **영문 약어** | "CI(Critical Illness)", "ADL(Activities of Daily Living)" | 보통 |

#### 한국어 NLP 처리의 구조적 어려움

한국어는 영어와 비교하여 자연어 처리에서 다음과 같은 추가적 어려움이 있다:

1. **형태소 분석의 복잡성**: 한국어의 교착어적 특성으로 하나의 단어에 여러 접사가 결합되어 의미가 변화 (예: "보상하다", "보상하지", "보상하였으나")
2. **띄어쓰기 비일관성**: 약관 문서에서도 띄어쓰기가 일관되지 않은 경우가 존재
3. **중의성**: 동일 단어가 맥락에 따라 다른 의미를 가질 수 있음 (예: "보험료"와 "보험금"의 혼동)
4. **어순의 유연성**: 한국어 문장의 어순이 영어보다 유연하여 파싱 난이도 증가

### 3.2 조항 간 상호 참조 구조

보험약관의 가장 큰 텍스트 처리 난제 중 하나는 **조항 간 상호 참조(cross-reference)** 구조이다.

#### 상호 참조 패턴 유형

```
[직접 참조]
"제15조(보험금의 청구)에 의한 서류를 제출받은 때에는..."

[간접 참조]
"제2관에서 정한 보험금 지급사유에 해당하는 경우..."

[별표 참조]
"【별표1】 '후유장해등급별 보상금액표'에서 정한 기준에 따라..."

[특약 참조]
"이 특약에서 정하지 않은 사항은 보통약관을 따릅니다."

[외부 법률 참조]
"「상법」 제663조 및 「보험업법」 제102조에 따라..."

[조건부 참조]
"다만, 제○조 제○항에 해당하는 경우를 제외합니다."
```

#### 상호 참조 처리의 중요성

- RAG 시스템에서 사용자가 특정 조항에 대해 질문하면, 해당 조항이 참조하는 다른 조항의 내용까지 함께 제공해야 정확한 답변이 가능
- 단순 텍스트 청킹으로는 참조 관계가 끊어지므로, **참조 관계 메타데이터**를 별도로 관리해야 함
- 참조 패턴을 정규표현식으로 감지하여 관계 그래프를 구축하는 것이 권장됨

### 3.3 별표/부표 등 부속 문서 처리

| 부속 문서 유형 | 특성 | 처리 난이도 |
|---------------|------|-----------|
| **장해분류표** | 계층적 표 구조, 퍼센트 수치, 의학 용어 포함 | 매우 높음 |
| **질병코드표** | KCD 코드 체계, 대량의 행(수백~수천 행) | 높음 |
| **보험료 산출표** | 다차원 표, 나이/성별/금액 매트릭스 | 높음 |
| **서식(청구서류 등)** | 양식 형태, 체크박스, 기입란 | 보통 |
| **보험금 지급기준표** | 조건별 지급률, 중첩 조건 | 높음 |

#### 부속 문서 처리 전략

1. **별표를 독립 청크로 분리**: 별표는 본문 조항과 분리하되, 메타데이터로 참조 관계를 유지
2. **표 데이터를 구조화된 형태로 저장**: JSON 또는 CSV 형태로 변환하여 별도 인덱싱
3. **계층적 표는 행 단위로 분해**: 각 행에 상위 분류 정보를 메타데이터로 부여하여 검색 가능성 확보

---

## 4. 청킹(Chunking) 전략 고려사항

### 4.1 보험약관에 적합한 청킹 방식

보험약관의 구조적 특성을 고려할 때, 일반적인 고정 크기 청킹보다 **구조 기반 청킹**이 훨씬 효과적이다.

#### 청킹 방식 비교

| 청킹 방식 | 적합도 | 장점 | 단점 |
|-----------|--------|------|------|
| **고정 크기 청킹** | 낮음 | 구현 단순 | 조항 경계 무시, 문맥 단절 |
| **조항 단위 청킹** | 높음 | 약관 구조와 일치, 의미 보존 | 조항 크기 편차가 큼 (1문장~수 페이지) |
| **계층적 청킹** | 매우 높음 | 관-조-항-호 계층 보존, 상위 맥락 유지 | 구현 복잡도 높음 |
| **의미 단위(Semantic) 청킹** | 높음 | 의미적 완결성 보장 | 보험 도메인 특화 모델 필요 |
| **슬라이딩 윈도우 + 구조 기반 하이브리드** | 매우 높음 | 조항 경계 유지 + 참조 맥락 보존 | 중복 저장으로 인한 스토리지 증가 |

#### 추천: 계층적 조항 기반 청킹

```
청킹 전략: 계층적 조항 기반 (Hierarchical Article-based Chunking)

Level 1: 관(Part) 단위 요약 청크
         예: "제2관 보험금의 지급" → 관 전체 요약

Level 2: 조(Article) 단위 상세 청크 ← 기본 검색 단위
         예: "제10조 (보험금의 종류와 지급사유)"

Level 3: 항/호(Paragraph/Subparagraph) 단위 세부 청크
         예: "제10조 제2항 제3호"

Level 4: 별표/부표 행 단위 청크
         예: "【별표1】 5급 장해 - 한쪽 눈의 시력 0.06 이하"
```

**핵심 원칙**:
- 조항(Article)을 기본 검색 단위로 설정
- 각 청크에 상위 계층 정보를 컨텍스트로 포함 (예: "제2관 > 제10조 > 제2항")
- 짧은 조항은 인접 조항과 병합하되, 최대 토큰 수 제한 준수 (권장: 512~1024 토큰)
- 긴 조항은 항/호 단위로 분할하되, 조항 제목과 목적을 각 청크 앞에 반복 삽입

### 4.2 메타데이터 활용 방안

RAG 시스템의 검색 정확도를 높이기 위해 각 청크에 풍부한 메타데이터를 부여해야 한다.

#### 필수 메타데이터 스키마

```json
{
  "chunk_id": "samsung_life_ci_2025_art10_p2",
  "document_metadata": {
    "insurance_company": "삼성생명",
    "product_name": "무배당 삼성 CI보험",
    "product_code": "SL-CI-2025-01",
    "document_type": "보통약관",
    "effective_date": "2025-04-01",
    "version": "2025년 4월 개정"
  },
  "structural_metadata": {
    "part": "제2관 보험금의 지급",
    "article": "제10조",
    "article_title": "보험금의 종류와 지급사유",
    "paragraph": "제2항",
    "subparagraph": null,
    "page_number": 15,
    "hierarchy_path": "보통약관 > 제2관 > 제10조 > 제2항"
  },
  "semantic_metadata": {
    "topic": "보험금 지급",
    "keywords": ["사망보험금", "지급사유", "보험기간"],
    "summary": "사망보험금의 지급사유와 지급금액을 정의",
    "category": "보장내용"
  },
  "reference_metadata": {
    "references_to": ["제2조", "제15조", "【별표1】"],
    "referenced_by": ["제20조", "특약 제5조"],
    "external_law_references": ["상법 제663조"]
  }
}
```

#### 메타데이터 기반 검색 전략

| 검색 유형 | 활용 메타데이터 | 예시 질의 |
|-----------|---------------|----------|
| **시맨틱 검색** | 임베딩 벡터 + keywords | "암 진단 시 보험금은 얼마인가요?" |
| **필터링 검색** | insurance_company, product_name | "삼성생명 CI보험에서..." |
| **구조 검색** | article, hierarchy_path | "제10조에 대해 알려주세요" |
| **참조 추적** | references_to, referenced_by | "면책사유와 관련된 모든 조항" |
| **버전 비교** | effective_date, version | "2024년과 2025년 약관의 차이점" |

#### 메타데이터 생성 자동화 방안

1. **정규표현식 기반 구조 파싱**: 조/항/호 번호, 별표 참조 등을 패턴 매칭으로 자동 추출
2. **LLM 기반 요약/키워드 생성**: 각 청크에 대해 LLM을 활용하여 summary, keywords 자동 생성
3. **참조 관계 그래프 구축**: 조항 간 참조 패턴을 감지하여 references_to/referenced_by를 자동 매핑
4. **문서 메타데이터 템플릿**: 보험사/상품별 메타데이터를 사전 정의하여 일괄 적용

---

## 5. 종합 권장사항 및 구현 로드맵

### 5.1 기술 스택 권장

| 단계 | 1순위 도구 | 2순위 보완 도구 | 용도 |
|------|-----------|---------------|------|
| PDF 텍스트 추출 | pymupdf4llm | pdfplumber | 일반 텍스트 + Markdown 변환 |
| 표(Table) 추출 | pdfplumber | pymupdf4llm (표 모드) | 정밀 표 데이터 추출 |
| OCR (필요시) | PaddleOCR / Surya OCR | EasyOCR | 스캔 문서/이미지 텍스트 변환 |
| 청킹 | 커스텀 계층적 청커 | LangChain RecursiveCharacterTextSplitter | 조항 구조 기반 분할 |
| 메타데이터 생성 | 정규표현식 + LLM 보조 | - | 구조/참조 메타데이터 자동화 |

### 5.2 구현 단계별 로드맵

```
Phase 1: PDF 파싱 파이프라인 구축
  - pymupdf4llm 기반 텍스트/표 추출 구현
  - PDF 유형(텍스트/스캔) 자동 감지 로직 구현
  - OCR 폴백 처리 (스캔 PDF 대응)

Phase 2: 구조 분석 및 청킹
  - 정규표현식 기반 약관 구조 파서 개발 (관/조/항/호/별표)
  - 계층적 조항 기반 청킹 엔진 구현
  - 상호 참조 관계 감지 및 그래프 구축

Phase 3: 메타데이터 체계 구축
  - 메타데이터 스키마 확정 및 자동 추출 파이프라인
  - LLM 기반 요약/키워드 보강
  - 벡터 DB 인덱싱 (메타데이터 필터링 지원)

Phase 4: 품질 검증 및 최적화
  - 추출 정확도 검증 (원본 대비 텍스트 일치율)
  - 청킹 품질 평가 (검색 적합성 테스트)
  - 엣지 케이스 처리 (깨진 표, 특수문자, 이미지 내 텍스트 등)
```

### 5.3 주요 리스크 및 완화 방안

| 리스크 | 영향도 | 완화 방안 |
|--------|--------|----------|
| PDF 형식 다양성 (보험사별 상이한 포맷) | 높음 | 보험사별 파서 템플릿 구성, 점진적 확장 |
| 표 추출 실패 (복잡한 병합 셀, 경계선 없는 표) | 중간 | pdfplumber 우선, 실패 시 이미지 변환 후 OCR 보완 |
| 상호 참조 누락 | 높음 | 정규표현식 패턴 라이브러리 확충, 수동 검증 병행 |
| OCR 인식 오류 (스캔 문서) | 중간 | 신뢰도 점수 기반 필터링, 사후 교정 로직 |
| 약관 업데이트에 따른 버전 관리 | 중간 | effective_date 기반 버전 관리, 변경 이력 추적 |

---

## 6. 참고 자료

### 라이브러리 및 도구
- [PyMuPDF4LLM 공식 문서](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [PyMuPDF4LLM GitHub](https://github.com/pymupdf/pymupdf4llm)
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [PyMuPDF 기능 비교](https://pymupdf.readthedocs.io/en/latest/about.html)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [Surya OCR GitHub](https://github.com/datalab-to/surya)
- [py-pdf/benchmarks - PDF 라이브러리 벤치마크](https://github.com/py-pdf/benchmarks)

### PDF 파싱 및 비교 분석
- [A Comparative Study of PDF Parsing Tools Across Diverse Document Categories (arXiv)](https://arxiv.org/html/2410.09871v1)
- [I Tested 7 Python PDF Extractors (2025 Edition) - Medium](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- [파이썬 PDF 텍스트 추출 라이브러리 3종 비교 - Medium](https://medium.com/@qpark99/%ED%8C%8C%EC%9D%B4%EC%8D%AC-pdf-%ED%85%8D%EC%8A%A4%ED%8A%B8-%EC%B6%94%EC%B6%9C-%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC-3%EC%A2%85-%EB%B9%84%EA%B5%90-4460d7cf3f63)
- [RAG/LLM and PDF: Conversion to Markdown Text with PyMuPDF - Artifex](https://artifex.com/blog/rag-llm-and-pdf-conversion-to-markdown-text-with-pymupdf)

### OCR 성능 비교
- [Tesseract vs EasyOCR: Real Results (2025)](https://www.codesota.com/ocr/tesseract-vs-easyocr)
- [OCR 성능 평가: 8가지 파이썬 API 비교 테스트](https://sooeun67.github.io/data%20science/ocr-comparison/)
- [PaddleOCR vs Tesseract: Best Open Source OCR](https://www.koncile.ai/en/ressources/paddleocr-analyse-avantages-alternatives-open-source)
- [8 Top Open-Source OCR Models Compared](https://modal.com/blog/8-top-open-source-ocr-models-compared)

### 청킹 및 RAG 전략
- [kt cloud AI RAG - 청킹 전략과 최적화](https://tech.ktcloud.com/entry/2025-11-ktcloud-rag-ai-%EC%B2%AD%ED%82%B9%EC%A0%84%EB%9E%B5-%EC%B5%9C%EC%A0%81%ED%99%94)
- [Amazon Bedrock Knowledge Bases - 분할 전략으로 검색 성능 최적화](https://aws.amazon.com/ko/blogs/tech/amazon-bedrock-knowledge-bases-optimizing-search-with-data-driven-chunking/)
- [RAG의 핵심: 데이터 구조화와 청킹 기술의 진화 - SelectStar](https://selectstar.ai/blog/insight/rag-chunking-ko/)
- [Chunking Strategies for RAG - Weaviate](https://weaviate.io/blog/chunking-strategies-for-rag)
- [Best Chunking Strategies for RAG in 2025 - Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
- [Bridging Legal Knowledge and AI: RAG with Vector Stores and Knowledge Graphs (arXiv)](https://arxiv.org/html/2502.20364v2)

### 한국어 NLP 및 보험 도메인
- [한국어 자연어처리가 어려운 이유 - FastCampus](https://fastcampus.co.kr/story_article_nlp)
- [한국어 전처리 패키지 - 딥러닝 자연어 처리 입문](https://wikidocs.net/92961)
- [보험약관 해석 기준 연구 - 보험연구원](https://www.kiri.or.kr/report/downloadFile.do?docId=209239)
- [RAG + Document Processing for Insurance - A21.ai](https://a21.ai/rag-document-processing-is-the-new-tech-to-boost-insurance/)
- [Advanced RAG: Automated Structured Metadata Enrichment - Haystack](https://haystack.deepset.ai/cookbook/metadata_enrichment)

### 보험약관 공시 사이트
- [생명보험협회](https://www.klia.or.kr/)
- [DB손해보험 약관 다운로드](https://www.idbins.com/FWMAIV1534.do)
- [KB손해보험 상품목록(약관)](https://www.kbinsure.co.kr/CG802030001.ec)
