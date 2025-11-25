#!/usr/bin/env bash
set -euo pipefail
# TODO: extrair PDF -> texto (pdftotext / tesseract se precisar)
# TODO: limpar cabeçalho/rodapé; normalizar whitespace
# TODO: segmentar por Art./Cap./Seção
# TODO: chunking (CHUNK_SIZE=700, OVERLAP=80) -> data/processed/chunks.jsonl
# TODO: salvar QA (n_chunks, histograma de tokens) em data/processed/qa.json
echo "[TODO] prepare_data conforme INGESTION_PLAN.md"
