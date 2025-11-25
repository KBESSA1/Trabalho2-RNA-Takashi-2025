#!/usr/bin/env bash
set -euo pipefail
# TODO: carregar eval/configs/perguntas_eval.json
# TODO: para cada pergunta -> recuperar top-k -> montar prompt -> gerar resposta -> quebrar em sentenças
# TODO: NLI por sentença (mDeBERTa-v3-mnli-xnli) vs contextos -> Fact Score
# TODO: salvar CSV em eval/results/factscore.csv e resumo em eval/results/summary.json (+ plot.png)
echo "[TODO] run_eval (Fact Score) conforme EVAL_PLAN.md"
