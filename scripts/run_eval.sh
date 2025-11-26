#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/rag-facom

echo "[eval] Rodando avaliação de Fact Score..."
python eval/run_fact_score.py

echo "[eval] Avaliação concluída. Veja o arquivo eval/results_factscore.csv."
