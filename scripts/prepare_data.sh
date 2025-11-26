#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/processed

PDF="$(ls -1 data/raw/*.pdf 2>/dev/null | head -n1 || true)"
TXT="$(ls -1 data/raw/*.txt 2>/dev/null | head -n1 || true)"

if [ -n "${PDF}" ]; then
  echo "[prepare] extraindo texto de: ${PDF}"
  pdftotext -layout "$PDF" data/processed/texto.txt || true
  if [ ! -s data/processed/texto.txt ]; then
    echo "[prepare] pdftotext vazio; tentativa de OCR (1ª página)"
    mkdir -p data/processed/ocr
    pdftoppm -f 1 -l 1 -png "$PDF" data/processed/ocr/page
    tesseract data/processed/ocr/page-1.png data/processed/ocr/page-1 -l por || true
    [ -f data/processed/ocr/page-1.txt ] && cp data/processed/ocr/page-1.txt data/processed/texto.txt
  fi
elif [ -n "${TXT}" ]; then
  echo "[prepare] usando texto puro: ${TXT}"
  cp "${TXT}" data/processed/texto.txt
else
  echo "[ERRO] Coloque REGULAMENTO.pdf (ou .txt) em data/raw/"
  exit 1
fi

# chunking placeholder (você implementa depois)
echo "{}" > data/processed/chunks.jsonl
echo '{"n_chunks":0,"note":"placeholder; implementar chunking"}' > data/processed/qa.json

echo "[OK] gerados: data/processed/texto.txt, chunks.jsonl, qa.json"
