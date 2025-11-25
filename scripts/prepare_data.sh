#!/usr/bin/env bash
set -euo pipefail
PDF="$(ls -1 data/raw/*.pdf 2>/dev/null | head -n1 || true)"
[ -z "${PDF}" ] && { echo "ERRO: coloque o PDF em data/raw/"; exit 1; }

mkdir -p data/processed
# Extrai texto simples (sem layout); se for escaneado, depois usamos tesseract
pdftotext -layout "$PDF" data/processed/texto.txt || true

if [ ! -s data/processed/texto.txt ]; then
  echo "[aviso] pdftotext vazio; tentando OCR por página..."
  mkdir -p data/processed/ocr
  # exemplo OCR 1ª página (ajuste depois p/ loop)
  pdftoppm -f 1 -l 1 -png "$PDF" data/processed/ocr/page
  tesseract data/processed/ocr/page-1.png data/processed/ocr/page-1 -l por
  cat data/processed/ocr/page-1.txt > data/processed/texto.txt
fi

# placeholders de chunking (a lógica virá depois)
echo "{}" > data/processed/chunks.jsonl
echo '{"n_chunks":0,"note":"placeholder; implementar chunking"}' > data/processed/qa.json

echo "[OK] texto e placeholders gerados em data/processed/"
