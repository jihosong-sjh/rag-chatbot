.PHONY: install parse index run evaluate test

install:
	uv sync

install-dev:
	uv sync --extra dev

install-reranker:
	uv sync --extra reranker

parse:
	uv run python scripts/01_parse_pdfs.py

index:
	uv run python scripts/02_build_index.py

run:
	uv run python scripts/03_run_rag.py

evaluate:
	uv run python scripts/04_evaluate.py

test:
	uv run pytest tests/ -v
