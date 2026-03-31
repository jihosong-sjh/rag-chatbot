# 보험 RAG 챗봇 - 관련 논문 및 RAG 아키텍처 조사

> 작성일: 2026-03-31
> 목적: 보험약관 RAG 챗봇 프로젝트를 위한 도메인 리서치

---

## 목차

1. [관련 학술 논문](#1-관련-학술-논문)
2. [도메인 특화 RAG 아키텍처](#2-도메인-특화-rag-아키텍처)
3. [한국어 특화 고려사항](#3-한국어-특화-고려사항)
4. [평가 방법론](#4-평가-방법론)
5. [종합 권장사항](#5-종합-권장사항)

---

## 1. 관련 학술 논문

### 1.1 보험 도메인 RAG/QA 논문

#### (1) A Korean Legal Judgment Prediction Dataset for Insurance Disputes (2024)
- **출처**: [arXiv 2401.14654](https://arxiv.org/abs/2401.14654)
- **핵심 내용**: 한국 보험 분쟁에 대한 법적 판결 예측 데이터셋 구축
- **데이터셋**: 금융감독원 및 한국소비자원에서 수집한 473건의 보험 분쟁 사례(231K 토큰)
  - 구성: 객관적 사실(facts), 당사자 주장(claims), 이진 레이블(조정 결과)
  - 클래스 불균형: 신청인 유리 287건 vs 피신청인 유리 186건
- **방법론**: SetFit(Sentence Transformer Fine-tuning) 활용
  - SetFit + paraphrase-mpnet-base-v2: **정확도 70.5%** (최고 성능)
  - SVM: 64.5%, kobigbird-bert-base 파인튜닝: 64.2%
- **시사점**: 소규모 데이터에서 SetFit이 표준 파인튜닝 대비 효율적. 한국어 보험 분쟁 NLP의 가능성 입증

#### (2) Multi-Module AI System for Health Insurance Support Using RAG (2025)
- **출처**: [Nature Scientific Reports](https://www.nature.com/articles/s41598-025-31038-6)
- **핵심 내용**: RAG 기반 다중 모듈 AI 시스템으로 건강보험 정보 상호작용 간소화
- **아키텍처**: 3개 모듈 통합
  - 챗봇 모듈: 일반 보험 질의 응답
  - 보험 추천 엔진: 구조화/비구조화 보험 데이터 활용 RAG
  - 문서 검색 모듈: 업로드된 보험약관에서 조항 수준 검색
- **성과**:
  - 의미 검색 BERTScore F1: **0.84**
  - 추천 Hit@5: **1.0**, Recall@5: **0.833**
  - 약관 조항 검색 BERTScore F1: **0.8443**

#### (3) Benchmarking LLMs for Quebec Insurance: Closed-Book to RAG (2025)
- **출처**: [arXiv 2603.07825](https://arxiv.org/abs/2603.07825)
- **핵심 내용**: 보험 도메인 LLM 벤치마크 (AEPC-QA)
  - 807개 객관식 질문, 51개 LLM 평가
  - RAG가 약한 모델의 정확도를 **35%p 이상** 향상 ("지식 평등화" 효과)
  - 일부 모델에서는 "컨텍스트 혼란(context distraction)" 으로 오히려 성능 하락 발생
- **시사점**: RAG 도입 시 모델별 특성을 고려해야 하며, 맹목적 RAG 적용은 위험

#### (4) Industrial-Scale Insurance LLM: Verifiable Domain Mastery (2025)
- **출처**: [arXiv 2603.14463](https://arxiv.org/html/2603.14463)
- **핵심 내용**: INSEva 벤치마크 - 보험 산업 최대 규모 평가 체계
  - 39,000개 샘플, 9개 핵심 차원, 50개 이상 태스크 유형
  - "LLM-as-a-Judge" 자동 평가 파이프라인 활용
  - 할루시네이션 제어와 도메인 전문성 간 트레이드오프 없는 모델 달성

### 1.2 법률 도메인 RAG 논문

#### (5) Towards Comprehensive Legal Document Analysis: Multi-Round RAG (2025)
- **출처**: [ACM ICMR 2025](https://dl.acm.org/doi/10.1145/3731715.3733451)
- **핵심 내용**: 법률 문서의 포괄적 분석을 위한 다중 라운드 RAG 접근법

#### (6) JusBuild: Enhancing Legal Document Building with RAG (2025)
- **출처**: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2212473X25001014)
- **핵심 내용**: 법률 문서 작성 지원 RAG 아키텍처
  - CRF 모델을 이용한 법률 문서 지도학습 기반 세분화
  - 세분화된 섹션의 의미 표현을 벡터 데이터베이스에 저장
  - RAG + LLM으로 관련 선례 섹션 제안 및 새 콘텐츠 생성

#### (7) LRAGE: Legal RAG Evaluation Tool (2025)
- **출처**: [arXiv 2504.01840](https://arxiv.org/html/2504.01840v1)
- **핵심 내용**: 법률 도메인 RAG 시스템 체계적 평가 프레임워크
- **평가 5대 요소**: 검색 코퍼스, 검색 알고리즘, 리랭커, LLM 백본, 평가 지표
- **주요 발견**:
  - 도메인 특화 법률 코퍼스가 Wikipedia 등 범용 자원보다 유의미하게 우수
  - Dense retriever는 법률 분야에서 BM25 수준 달성을 위해 상당한 도메인 적응 필요
  - 리랭커 효과는 태스크/코퍼스별로 상이하므로 실증 평가 필수
  - 기성 에이전틱 RAG가 자동으로 성능을 개선하지는 않음

#### (8) Benchmarking KG-based RAG: Legal Documents Case Study
- **출처**: [CEUR Workshop Proceedings](https://ceur-ws.org/Vol-4079/paper6.pdf)
- **핵심 내용**: 지식 그래프(KG) 기반 RAG의 법률 문서 적용 벤치마크

### 1.3 한국어 법률 NLP 논문

#### (9) KBL: Pragmatic Benchmark for Korean Legal Language Understanding (2024)
- **출처**: [arXiv 2410.08731](https://arxiv.org/html/2410.08731v1) / [EMNLP 2024 Findings](https://aclanthology.org/2024.findings-emnlp.319.pdf)
- **핵심 내용**: 한국어 법률 언어 이해 평가 벤치마크
  - 7개 법률 지식 태스크 (510 예제)
  - 4개 법률 추론 태스크 (288 예제)
  - 한국 변호사시험 기반 4개 도메인, 53개 태스크 (2,510 예제)

#### (10) Legal Text Classification in Korean Sexual Offense Cases (2025)
- **출처**: [Springer AI and Law](https://link.springer.com/article/10.1007/s10506-025-09454-w)
- **핵심 내용**: 전통 ML부터 LLM까지의 법률 텍스트 분류 비교
  - KLUE-BERT 등 파인튜닝된 소형 모델이 대형 범용 모델보다 우수한 성능

#### (11) CALRK-Bench: Context-Aware Legal Reasoning in Korean Law (2025)
- **출처**: [arXiv 2603.26332](https://arxiv.org/html/2603.26332)
- **핵심 내용**: 한국 법률에서의 문맥 인식 법적 추론 평가 벤치마크

### 1.4 한국 보험 RAG 구현 사례

#### 검색 증강 생성을 이용한 LangChain 기반 보험 FAQ 상담 챗봇 (2025)
- **출처**: [한국정보통신학회논문지 (KCI)](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003204819)
- **핵심 내용**: LangChain 프레임워크와 RAG를 활용한 보험 FAQ 고객 상담 챗봇 설계 및 구현

#### 교보라이프플래닛생명 사례
- Claude 3.5와 최신 RAG 기술 기반 "생성형 AI 기반 채팅 상담 세일즈 플랫폼" 개발
- AWS 클라우드 기반, 금융위원회 "2025년 혁신금융서비스" 지정

---

## 2. 도메인 특화 RAG 아키텍처

### 2.1 RAG 패러다임 비교: Naive vs Advanced vs Modular

#### 참고 논문
- [Modular RAG: Transforming RAG Systems into LEGO-like Reconfigurable Frameworks](https://arxiv.org/html/2407.21059v1)
- [Zilliz: Native, Advanced, Modular RAG Approaches](https://zilliz.com/blog/advancing-llms-native-advanced-modular-rag-approaches)

#### Naive RAG

| 항목 | 내용 |
|------|------|
| **구조** | 인덱싱 -> 검색 -> 생성 ("Retrieve-Read" 프레임워크) |
| **장점** | 구현 간단, 빠른 프로토타이핑 |
| **한계** | 쿼리의 피상적 이해, 유사도만으로 검색하여 심층적 관계 탐색 부족 |
| **적합 용도** | PoC, 단순 FAQ 봇 |

#### Advanced RAG

| 항목 | 내용 |
|------|------|
| **구조** | 사전 검색 최적화 + 검색 + 사후 검색 최적화 + 생성 |
| **사전 검색** | 쿼리 확장(Query Expansion), 쿼리 재작성(Query Rewriting) |
| **사후 검색** | 리랭킹(Reranking), 필터링(Filtering), 압축(Compression) |
| **장점** | Naive RAG 대비 정밀한 제어 가능, 검색 정확도 향상 |
| **적합 용도** | 중간 복잡도의 프로덕션 시스템 |

#### Modular RAG

| 항목 | 내용 |
|------|------|
| **구조** | 모듈 -> 서브모듈 -> 연산자의 3계층 구조 |
| **6대 모듈** | 인덱싱, 사전 검색, 검색, 사후 검색, 생성, 오케스트레이션 |
| **흐름 패턴** | 선형(Linear), 조건부(Conditional), 분기(Branching), 반복(Loop), 튜닝(Tuning) |
| **장점** | LEGO 블록처럼 재구성 가능, 각 모듈 독립적 디버깅/최적화 |
| **적합 용도** | 복잡한 실세계 애플리케이션, 다중 도메인 |

#### 보험약관 RAG에 대한 권장사항

보험약관 RAG 챗봇에는 **Advanced RAG**를 기본으로 하되, 향후 확장을 위해 **Modular RAG** 설계 원칙을 적용하는 것을 권장한다.

이유:
1. 보험약관은 구조화된 문서이므로 구조 기반 인덱싱이 필수
2. 법률 용어의 정확한 매칭을 위해 하이브리드 검색(BM25 + Dense) 필요
3. 사용자 질의의 모호성 해소를 위해 쿼리 재작성 단계 필요
4. 할루시네이션 방지를 위해 사후 검색 검증 단계 필요

### 2.2 보험약관 특화 RAG 파이프라인 설계 제안

```
[사용자 질의]
    |
    v
[1. 쿼리 처리 모듈]
    - 한국어 형태소 분석
    - 보험 용어 인식 및 정규화
    - 쿼리 재작성 / 확장
    |
    v
[2. 하이브리드 검색 모듈]
    - BM25 (정확한 용어 매칭, 약관 번호/조항명)
    - Dense Retrieval (의미 기반 검색)
    - RRF(Reciprocal Rank Fusion)로 결과 통합
    |
    v
[3. 리랭킹 모듈]
    - Cross-Encoder 기반 리랭킹
    - 보험약관 메타데이터 활용 필터링
    |
    v
[4. 컨텍스트 구성 모듈]
    - 검색 결과 압축 및 선별
    - 관련 조항 간 참조 관계 구성
    |
    v
[5. 생성 모듈]
    - LLM 기반 답변 생성
    - 출처(약관 조항) 명시
    - 할루시네이션 검증
    |
    v
[답변 + 출처 정보]
```

### 2.3 하이브리드 검색 전략

보험약관은 법률 용어와 자연어가 혼합된 특수한 문서이므로, 하이브리드 검색이 필수적이다.

#### BM25 (희소 검색)의 역할
- **정확한 용어 매칭**: "제3조 보험금의 지급사유", "면책사항" 등 특정 조항/용어 검색
- **약관 번호 기반 검색**: 사용자가 구체적인 조항 번호를 언급할 때
- **희귀 용어 처리**: 도메인 특화 용어는 임베딩 모델이 충분히 학습하지 못했을 수 있음

#### Dense Retrieval (밀집 검색)의 역할
- **의미 기반 검색**: "암 진단받으면 보험금 받을 수 있나요?" -> 관련 보장 조항 검색
- **동의어/유사 표현 처리**: "가입자" = "보험계약자" = "피보험자" 등

#### 결합 방법: RRF (Reciprocal Rank Fusion)
- 참고: [Superlinked - Optimizing RAG with Hybrid Search & Reranking](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- BM25와 Dense Retrieval 결과를 RRF로 통합하여 두 방법의 장점을 결합
- 가중치 조절을 통해 도메인에 최적화된 검색 결과 도출

### 2.4 리랭킹(Reranking) 전략

참고:
- [Analytics Vidhya: Top 7 Rerankers for RAG (2025)](https://www.analyticsvidhya.com/blog/2025/06/top-rerankers-for-rag/)
- [IBM: How ColBERT Re-ranker Works](https://developer.ibm.com/articles/how-colbert-works/)

#### 리랭킹 방식 비교

| 방식 | 특징 | 장점 | 단점 |
|------|------|------|------|
| **Cross-Encoder** | 쿼리-문서 쌍을 함께 인코딩하여 토큰 수준 관련성 점수 계산 | 가장 높은 정확도 | 추론 속도 느림 (소규모 후보에만 적합) |
| **ColBERT (Late Interaction)** | 쿼리/문서 독립 인코딩 후 MaxSim 스코어링 | 문서 표현 사전 계산 가능, 빠른 검색 | Cross-Encoder 대비 약간 낮은 정확도 |
| **Bi-Encoder** | 쿼리/문서 독립 인코딩 후 코사인 유사도 | 가장 빠름 | 세밀한 관련성 판단 제한적 |

#### 보험약관 RAG 권장 전략: 2단계 검색

```
1단계: 하이브리드 검색 (BM25 + Dense) -> Top-K 후보 (예: 20개)
2단계: Cross-Encoder 리랭킹 -> Top-N 최종 결과 (예: 5개)
```

- 1단계에서 효율적으로 넓은 범위의 후보를 확보
- 2단계에서 정밀한 관련성 평가로 최종 결과 선별
- 프로덕션에서 지연시간(latency) 요구사항에 따라 ColBERT 대안 검토

#### 추천 리랭킹 모델
- **Jina Reranker v2**: 다국어 지원, RAG 파이프라인 통합 용이
- **Cohere Rerank**: API 기반, 한국어 지원
- **BGE Reranker**: 오픈소스, BGE 임베딩과 호환성 우수
- **ms-marco-MiniLM-L-12-v2 Cross-Encoder**: 경량 오픈소스 옵션

---

## 3. 한국어 특화 고려사항

### 3.1 한국어 임베딩 모델 현황

참고:
- [KURE-v1 (Hugging Face)](https://huggingface.co/nlpai-lab/KURE-v1)
- [BGE-M3 (Hugging Face)](https://huggingface.co/BAAI/bge-m3)
- [Korean Embedding Model Performance Benchmark (GitHub)](https://github.com/ssisOneTeam/Korean-Embedding-Model-Performance-Benchmark-for-Retriever)

#### 주요 한국어 임베딩 모델 비교

| 모델 | 개발사 | 차원 | 최대 토큰 | 파라미터 | Recall@1 | 특징 |
|------|--------|------|-----------|----------|----------|------|
| **KURE-v1** | 고려대 NLP Lab | 1024 | 8192 | 0.6B | **0.5264** | 한국어 검색 특화, BGE-M3 파인튜닝 |
| **dragonkue/BGE-m3-ko** | - | 1024 | 8192 | 0.6B | 0.5236 | BGE-M3 한국어 파인튜닝 |
| **BAAI/bge-m3** | BAAI | 1024 | 8192 | 0.6B | 0.5178 | 100+ 언어 지원, 밀집/희소/다중벡터 검색 |
| **nlpai-lab/KoE5** | 고려대 NLP Lab | 1024 | 512 | - | 0.5016 | 한국어 E5 파인튜닝 |
| **multilingual-e5-large** | Microsoft | 1024 | 512 | - | 0.5005 | 다국어 범용 |
| **ko-sroberta-multitask** | - | 768 | 512 | - | - | QA 기반 검색에서 최고 Hitrate |

#### 모델 선택 권장사항

**1순위: KURE-v1**
- 한국어 검색 최적화 모델로, 전체 벤치마크에서 1위
- BGE-M3 기반 파인튜닝으로 8192 토큰까지 처리 가능 (긴 약관 문서에 유리)
- MIT 라이선스, 오픈소스
- NDCG@1: 0.6055, Recall@10: 0.7968

**2순위: BGE-M3**
- 100개 이상 언어 지원으로 다국어 확장 가능
- 밀집(Dense), 희소(Sparse), 다중벡터(Multi-Vector) 검색 모두 지원
- 하이브리드 검색 구축 시 단일 모델로 Dense + Sparse 모두 커버 가능

**3순위: Qwen-3-Embedding (2025 신규)**
- 참고: [Qwen-3 vs BGE-M3 비교 분석 (Medium)](https://medium.com/@mrAryanKumar/comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retrieval-72c0e6895413)
- 다국어 RAG 시스템의 기본 선택으로 부상
- 고정밀도 요구 시 Qwen-3-4B, 일반 용도 시 Qwen-3-0.6B

**보험약관 RAG에 대한 최종 권장:**
- **KURE-v1**을 기본 임베딩 모델로 사용
- 하이브리드 검색 시 BGE-M3의 희소 벡터(Sparse) 기능 또는 별도 BM25와 결합
- 도메인 적응(Domain Adaptation)을 위해 보험약관 데이터로 추가 파인튜닝 검토

### 3.2 한국어 법률/보험 용어 처리

#### 핵심 과제

1. **전문 용어의 다양한 표현**
   - "보험계약자" = "계약자" = "가입자"
   - "보험금" = "보험급여" = "급부금"
   - "면책사유" = "면책조항" = "보상 제외 사항"

2. **법률 특유의 문체**
   - 조건절 중첩: "~한 경우에 한하여 ~할 수 있다"
   - 예외 조항: "다만, ~의 경우에는 그러하지 아니하다"
   - 참조 표현: "제O조에 따른", "별표 O에서 정한"

3. **한자어/외래어 혼용**
   - "피보험자(被保險者)", "면책(免責)", "실손보상(實損補償)"

#### 처리 전략

1. **보험 도메인 사전 구축**
   - 보험 용어 동의어 사전 (synonym dictionary)
   - 약어 확장 사전
   - 보험 상품 유형별 용어 매핑

2. **형태소 분석 최적화**
   - 한국어 형태소 분석기(Mecab-ko, Kiwi 등)에 보험 도메인 사용자 사전 추가
   - 복합 명사 처리: "보험금지급사유" -> "보험금 + 지급 + 사유"

3. **쿼리 확장(Query Expansion)**
   - 사용자의 일상 표현을 법률/보험 용어로 매핑
   - 예: "보험 해지하면 돈 돌려받을 수 있나요?" -> "보험계약 해지 환급금"

### 3.3 한국어 청크 분할(Chunking) 시 고려사항

참고:
- [kt cloud RAG 청킹 전략과 최적화](https://tech.ktcloud.com/entry/2025-11-ktcloud-rag-ai-%EC%B2%AD%ED%82%B9%EC%A0%84%EB%9E%B5-%EC%B5%9C%EC%A0%81%ED%99%94)
- [피카부랩스: RAG 청킹 전략 실증 분석](https://peekaboolabs.ai/blog/rag-chunking-strategy-analysis)
- [Hugging Face: 한국어 Advanced RAG 쿡북](https://huggingface.co/learn/cookbook/ko/advanced_ko_rag)

#### 한국어 텍스트의 특수성

1. **정보 밀도**: 한국어는 영어보다 정보 밀도가 높아, 동일 의미를 더 짧은 텍스트로 표현
   - 영어 기준 chunk size를 그대로 적용하면 과도하게 큰 청크가 됨
   - **권장**: 한국어 500~1,000자 (영어의 1,000~2,000자에 해당)

2. **토큰화 차이**: 한국어는 서브워드 토큰화 시 영어보다 더 많은 토큰 소모
   - BPE 기반 토크나이저에서 한국어 1글자 = 2~3 토큰
   - 토큰 기반 청크 크기 설정 시 이를 반영해야 함

3. **문장 경계**: 한국어는 문장 종결어미("~다", "~요")로 문장 경계가 비교적 명확

#### 보험약관 청킹 전략 권장사항

| 전략 | 설명 | 권장 여부 |
|------|------|-----------|
| **구조 기반 청킹** | 약관의 조/항/목 단위로 분할 | **강력 추천** |
| **시맨틱 청킹** | 의미적 유사도 기반 경계 설정 | 보조적 활용 |
| **고정 크기 청킹** | 일정 토큰/문자 단위 균등 분할 | 단독 사용 비권장 |
| **재귀적 청킹** | 계층적 구분자 기반 분할 | 구조 기반의 대안 |

#### 보험약관 구조 기반 청킹 예시

```
[보험약관 문서]
├── 제1관 일반사항
│   ├── 제1조 (보험용어의 정의) -> Chunk 1
│   ├── 제2조 (보험금의 지급사유) -> Chunk 2
│   └── 제3조 (보험금을 지급하지 않는 사유) -> Chunk 3
├── 제2관 보험금의 지급
│   ├── 제4조 (보험금 청구 절차) -> Chunk 4
│   └── ...
└── [별표] 보장 내용 표
    └── 별표1 (질병 분류표) -> Chunk N
```

**핵심 원칙:**
- 법률 문서의 조/항/목 구조를 최대한 유지
- 관련 조항 간 참조 관계를 메타데이터로 보존 (예: "제3조 참조" -> 해당 청크 연결)
- 청크 오버랩(Overlap) 적용으로 문맥 단절 방지 (10~20% 오버랩 권장)
- 별표, 부록 등은 별도 청크로 관리하되, 본문 조항과의 연결 메타데이터 유지

#### 청크 크기 도메인별 권장치

| 도메인 | 권장 청크 크기 (토큰) | 비고 |
|--------|----------------------|------|
| FAQ | 256 ~ 512 | 짧고 독립적인 QA 쌍 |
| **법률/보험 문서** | **800 ~ 1,500** | 조항 단위, 구조 보존 |
| 학술 문서 | 1,000 ~ 2,000 | 단락/섹션 단위 |
| 일반 문서 | 512 ~ 1,000 | 범용 |

> NVIDIA(2024) 벤치마크에서 페이지 단위 청킹이 7개 전략 중 평균 정확도 0.648로 최고 성능을 보였으나, 보험약관의 경우 조항 단위 청킹이 더 적합하다. 조항이 페이지 경계를 넘는 경우가 빈번하기 때문이다.

---

## 4. 평가 방법론

### 4.1 RAG 시스템 평가 프레임워크: RAGAS

참고:
- [RAGAS 공식 문서](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [RAGAS 논문 (arXiv 2309.15217)](https://arxiv.org/abs/2309.15217)
- [Maxim: Complete Guide to RAG Evaluation 2025](https://www.getmaxim.ai/articles/complete-guide-to-rag-evaluation-metrics-methods-and-best-practices-for-2025/)

#### RAGAS 핵심 지표

| 지표 | 설명 | 평가 대상 | 범위 |
|------|------|-----------|------|
| **Faithfulness** | 생성된 답변이 검색된 컨텍스트와 사실적으로 일치하는 정도 | 생성 품질 | 0~1 |
| **Answer Relevancy** | 생성된 답변이 질문에 얼마나 적절한지 | 생성 품질 | 0~1 |
| **Context Precision** | 검색된 컨텍스트 중 관련 항목이 상위에 위치하는 정도 | 검색 품질 | 0~1 |
| **Context Recall** | 정답을 도출하는 데 필요한 컨텍스트가 얼마나 검색되었는지 | 검색 품질 | 0~1 |
| **Context Relevance** | 검색된 컨텍스트가 질문에 얼마나 관련 있는지 | 검색 품질 | 0~1 |
| **Answer Accuracy** | 답변의 정확도 (ground truth 대비) | 생성 품질 | 0~1 |
| **Response Groundedness** | 응답이 제공된 컨텍스트에 근거하는 정도 | 생성 품질 | 0~1 |

#### RAGAS 평가 파이프라인

```
[질문(Query)] + [검색된 컨텍스트(Contexts)] + [생성된 답변(Answer)] + [정답(Ground Truth)]
    |
    v
[RAGAS 평가 엔진 (LLM-as-a-Judge)]
    |
    ├── Retrieval 평가: Context Precision, Context Recall
    ├── Generation 평가: Faithfulness, Answer Relevancy
    └── End-to-End: Answer Accuracy, Groundedness
```

### 4.2 보험 도메인 특화 평가 방법

#### INSEva 벤치마크 참고
- 9개 핵심 차원, 50개 이상 태스크 유형, 39,000개 샘플
- "LLM-as-a-Judge" 자동 평가 파이프라인

#### 보험약관 RAG 맞춤 평가 설계

| 평가 차원 | 지표 | 설명 |
|-----------|------|------|
| **조항 정확성** | Clause Accuracy | 인용된 약관 조항이 실제 존재하며 내용이 정확한지 |
| **법적 정확성** | Legal Precision | 법률 용어의 정확한 사용 여부 |
| **완전성** | Completeness | 질문에 관련된 모든 약관 조항이 참조되었는지 |
| **출처 추적성** | Traceability | 답변의 각 주장에 대한 약관 출처가 명시되었는지 |
| **사용자 이해도** | Readability | 일반 사용자가 이해할 수 있는 수준으로 설명되었는지 |
| **거절 적절성** | Refusal Quality | 약관에 없는 내용에 대해 적절히 "모른다"고 답하는지 |

#### 평가 데이터셋 구축 방안

1. **Gold Standard QA 세트**: 보험 전문가가 약관별 예상 QA 쌍 작성 (100~200쌍)
2. **엣지 케이스 세트**: 모호한 질문, 약관에 없는 질문, 다중 조항 참조 질문
3. **A/B 테스트 프레임워크**: 사용자 만족도 기반 정성 평가

### 4.3 Hallucination(할루시네이션) 방지 전략

참고:
- [MEGA-RAG (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12540348/)
- [Mindee: RAG Hallucinations Explained](https://www.mindee.com/blog/rag-hallucinations-explained)
- [You.com: AI Hallucination Prevention Guide](https://you.com/resources/ai-hallucination-prevention-guide)

#### 보험 도메인에서 할루시네이션이 특히 위험한 이유

- 보험금 지급/비지급에 대한 잘못된 안내는 **법적 분쟁**으로 이어질 수 있음
- 존재하지 않는 약관 조항 인용 시 **소비자 신뢰** 심각한 훼손
- 미국 법률 도메인 연구에서도 최고 성능 상용 RAG 시스템의 **할루시네이션 비율 17%** 보고

#### 다층적 할루시네이션 방지 아키텍처

```
[Layer 1: 검색 품질 확보]
  - 깨끗하고 최신인 검색 코퍼스 유지
  - 메타데이터 필터링으로 관련성 높은 결과만 선별
  - 검색 결과 신뢰도 임계값(threshold) 적용

[Layer 2: 생성 단계 제어]
  - 프롬프트에 "약관에 명시된 내용만 답변" 지시
  - 출처(조항 번호) 명시 의무화
  - 온도(Temperature) 낮게 설정 (0.0~0.1)

[Layer 3: 사후 검증]
  - Faithfulness 점수 기반 자동 검증
  - 인용된 조항이 실제 존재하는지 확인
  - 답변과 검색된 컨텍스트 간 의미적 일관성 검사

[Layer 4: 불확실성 표현]
  - 확신도가 낮은 경우 "확인이 필요합니다" 표현
  - 약관에 명시되지 않은 사항은 "해당 약관에서 확인되지 않습니다" 응답
  - 복잡한 사안은 전문 상담 안내
```

#### 핵심 기법

| 기법 | 설명 | 효과 |
|------|------|------|
| **다중 증거 검증 (MEGA-RAG)** | 다수결 투표, 문장 수준 클러스터링, 명확화 쿼리로 증거 일관성 확보 | 의미적 일관성, 근거 기반 출력 보장 |
| **Faithfulness 평가기** | LLM-as-a-Judge로 출력과 검색 컨텍스트 비교 | 사실 불일치 자동 탐지 |
| **Attribution 강제** | 모든 주장에 출처 명시 의무화 | 검증 가능한 답변 생성 |
| **Calibration Layer** | 모델의 불확실성을 표현하도록 학습 | 과신(overconfident) 생성 방지 |
| **Human-in-the-Loop** | 플래그된 출력을 사람이 검토 후 최종 승인 | 고위험 결정에 대한 안전망 |

---

## 5. 종합 권장사항

### 5.1 아키텍처 선택

| 요소 | 권장 | 근거 |
|------|------|------|
| **RAG 패러다임** | Advanced RAG (Modular RAG 원칙 적용) | 보험약관의 구조성과 정확성 요구를 충족 |
| **임베딩 모델** | KURE-v1 (1순위) / BGE-M3 (2순위) | 한국어 검색 벤치마크 최고 성능, 긴 문서 지원 |
| **검색 전략** | 하이브리드 (BM25 + Dense) + RRF | 정확한 용어 매칭과 의미 검색 결합 |
| **리랭킹** | Cross-Encoder (2단계 검색) | 소규모 후보 집합에서 정밀 관련성 평가 |
| **청킹** | 구조 기반 (조/항/목 단위) | 약관의 법적 구조 보존, 참조 관계 유지 |
| **평가** | RAGAS + 보험 도메인 맞춤 지표 | 표준 RAG 지표 + 조항 정확성, 출처 추적성 |

### 5.2 단계별 구현 로드맵

```
Phase 1: Naive RAG MVP
  - 단순 Dense Retrieval + LLM 생성
  - 기본 청킹 (고정 크기 + 구조 기반)
  - RAGAS 기본 지표로 베이스라인 측정

Phase 2: Advanced RAG
  - 하이브리드 검색 (BM25 + Dense) 도입
  - Cross-Encoder 리랭킹 추가
  - 쿼리 재작성 모듈
  - 보험 도메인 평가 세트 구축

Phase 3: 도메인 최적화
  - KURE-v1/BGE-M3 보험약관 파인튜닝
  - 보험 용어 사전 기반 쿼리 확장
  - 할루시네이션 다층 방지 체계
  - 구조 기반 청킹 고도화

Phase 4: 프로덕션
  - Modular RAG 전환 (확장성 확보)
  - 실시간 모니터링 및 피드백 루프
  - A/B 테스트 기반 지속적 개선
```

### 5.3 핵심 리스크 및 대응

| 리스크 | 대응 방안 |
|--------|-----------|
| 할루시네이션으로 인한 법적 문제 | 다층 검증, 면책 문구, Human-in-the-Loop |
| 한국어 임베딩 모델의 보험 용어 이해 부족 | 도메인 파인튜닝, 용어 사전 구축 |
| 약관 개정 시 검색 코퍼스 업데이트 지연 | 자동화된 인덱싱 파이프라인, 버전 관리 |
| 복잡한 다중 조항 질의 처리 | Multi-hop RAG, 조항 간 참조 그래프 |
| Context distraction (RAG가 오히려 방해) | 검색 결과 신뢰도 임계값, 선택적 RAG 적용 |

---

## 참고 문헌 및 출처

### 학술 논문
1. [A Korean Legal Judgment Prediction Dataset for Insurance Disputes (2024)](https://arxiv.org/abs/2401.14654)
2. [A Multi-Module AI System for Intelligent Health Insurance Support Using RAG (2025)](https://www.nature.com/articles/s41598-025-31038-6)
3. [Benchmarking LLMs for Quebec Insurance: Closed-Book to RAG (2025)](https://arxiv.org/abs/2603.07825)
4. [An Industrial-Scale Insurance LLM: INSEva Benchmark (2025)](https://arxiv.org/html/2603.14463)
5. [LRAGE: Legal RAG Evaluation Tool (2025)](https://arxiv.org/html/2504.01840v1)
6. [Modular RAG: LEGO-like Reconfigurable Frameworks (2024)](https://arxiv.org/html/2407.21059v1)
7. [M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity (2024)](https://arxiv.org/abs/2402.03216)
8. [KBL: Korean Legal Language Understanding Benchmark (2024)](https://arxiv.org/html/2410.08731v1)
9. [RAGAS: Automated Evaluation of RAG (2023)](https://arxiv.org/abs/2309.15217)
10. [CALRK-Bench: Context-Aware Legal Reasoning in Korean Law (2025)](https://arxiv.org/html/2603.26332)
11. [Legal Text Classification in Korean (2025)](https://link.springer.com/article/10.1007/s10506-025-09454-w)
12. [Towards Comprehensive Legal Document Analysis: Multi-Round RAG (2025)](https://dl.acm.org/doi/10.1145/3731715.3733451)
13. [JusBuild: Enhancing Legal Document Building with RAG (2025)](https://www.sciencedirect.com/science/article/pii/S2212473X25001014)
14. [MEGA-RAG: Multi-Evidence Guided Answer Refinement (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12540348/)
15. [RAG Hallucinations Explained (2025)](https://www.mindee.com/blog/rag-hallucinations-explained)
16. [Retrieval-Augmented Generation for Legal Work - Harvard JOLT](https://jolt.law.harvard.edu/digest/retrieval-augmented-generation-rag-towards-a-promising-llm-architecture-for-legal-work)

### 모델 및 도구
17. [KURE-v1 (Hugging Face)](https://huggingface.co/nlpai-lab/KURE-v1)
18. [BGE-M3 (Hugging Face)](https://huggingface.co/BAAI/bge-m3)
19. [RAGAS Documentation](https://docs.ragas.io/en/stable/)
20. [Korean Embedding Model Benchmark (GitHub)](https://github.com/ssisOneTeam/Korean-Embedding-Model-Performance-Benchmark-for-Retriever)
21. [Awesome Korean NLP Papers (GitHub)](https://github.com/papower1/Awesome-Korean-NLP-Papers)

### 기술 블로그 및 가이드
22. [kt cloud RAG 청킹 전략과 최적화 (2025)](https://tech.ktcloud.com/entry/2025-11-ktcloud-rag-ai-%EC%B2%AD%ED%82%B9%EC%A0%84%EB%9E%B5-%EC%B5%9C%EC%A0%81%ED%99%94)
23. [피카부랩스: RAG 청킹 전략 실증 분석](https://peekaboolabs.ai/blog/rag-chunking-strategy-analysis)
24. [Hugging Face 한국어 Advanced RAG 쿡북](https://huggingface.co/learn/cookbook/ko/advanced_ko_rag)
25. [Analytics Vidhya: Top 7 Rerankers for RAG (2025)](https://www.analyticsvidhya.com/blog/2025/06/top-rerankers-for-rag/)
26. [IBM: How ColBERT Re-ranker Works](https://developer.ibm.com/articles/how-colbert-works/)
27. [Superlinked: Optimizing RAG with Hybrid Search & Reranking](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
28. [Maxim: RAG Evaluation Guide 2025](https://www.getmaxim.ai/articles/complete-guide-to-rag-evaluation-metrics-methods-and-best-practices-for-2025/)
29. [한국정보통신학회: LangChain 기반 보험 FAQ 챗봇 (2025)](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003204819)
30. [MarkTechPost: Evolution of RAGs (2024)](https://www.marktechpost.com/2024/04/01/evolution-of-rags-naive-rag-advanced-rag-and-modular-rag-architectures/)
