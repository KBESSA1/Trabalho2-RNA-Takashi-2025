# RAG FACOM — Mini RAG + Fact Score
Reprodutível via Docker.
1) Coloque o PDF em `data/raw/`.
2) `docker compose up -d` (app/chroma/ollama).
3) Rode scripts de ingestão, index e avaliação (a serem implementados em `scripts/`).
4) Resultados serão salvos em `eval/results/`.
