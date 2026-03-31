"""전역 설정."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


# ── 경로 ──
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
CHUNKS_DIR = DATA_DIR / "chunks"
CHROMADB_DIR = DATA_DIR / "chromadb"
EVAL_DIR = ROOT_DIR / "eval_data"


class Settings(BaseSettings):
    """환경 변수 기반 설정."""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "exaone3.5:7.8b"

    # Claude (품질 검증용)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # 임베딩
    embedding_model: str = "nlpai-lab/KURE-v1"
    embedding_dim: int = 1024

    # 청킹
    chunk_min_tokens: int = 300
    chunk_max_tokens: int = 1500
    chunk_target_tokens: int = 1000

    # 검색
    retrieval_top_k: int = 20
    rerank_top_n: int = 5
    rrf_k: int = 60
    similarity_threshold: float = 0.3

    # 생성
    temperature: float = 0.0
    max_tokens: int = 2048

    model_config = {"env_file": str(ROOT_DIR / ".env"), "extra": "ignore"}


settings = Settings()
