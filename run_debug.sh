#!/usr/bin/env bash
# NÃO use set -e aqui.
set -u

ts="$(date +%Y%m%d-%H%M%S)"
LOG="logs/run_${ts}.log"

run() {
  echo; echo "---- EXEC: $*" | tee -a "$LOG"
  "$@"; rc=$?
  echo "---- RC=$rc" | tee -a "$LOG"
  return $rc
}

{
  echo "==[0] Contexto ==" 
  echo "PWD=$(pwd)"
  echo "User=$(whoami)"
  echo "Data=$(date)"
  echo

  echo "==[1] Conferindo PDF ==" 
  ls -lh data/raw/REGULAMENTO.pdf || { echo "[ERRO] cadê data/raw/REGULAMENTO.pdf?"; exit 1; }

  echo "==[2] Prepare ==" 
  run make prepare || echo "[AVISO] prepare retornou erro"

  echo "Preview do texto extraído (5 linhas):"
  head -n 5 data/processed/texto.txt || true

  echo "==[3] Chunk ==" 
  run make chunk || echo "[AVISO] chunk retornou erro"
  wc -l data/processed/chunks.jsonl 2>/dev/null || true
  cat data/processed/qa.json 2>/dev/null || true

  echo "==[4] Index (limpa índice local antes) ==" 
  rm -rf chroma_local
  run make index || echo "[AVISO] index retornou erro"
  if [ -d chroma_local ]; then du -sh chroma_local || true; fi

  echo "==[5] Pergunta de smoke ==" 
  if [ -f scripts/ask.py ]; then
    run python scripts/ask.py "Quais são os prazos para defesa?" || echo "[AVISO] ask falhou"
  else
    echo "[ERRO] scripts/ask.py não existe"
  fi

  echo
  echo "==[FIM] LOG salvo em $LOG =="
} 2>&1 | tee -a "$LOG"

echo
read -p "Pressione ENTER para manter o terminal aberto..."
