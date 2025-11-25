- Entrada: eval/configs/perguntas_eval.json
- Para cada pergunta:
  1) recuperar top-k no Chroma
  2) montar prompt (app/prompts/base.md + contextos)
  3) gerar resposta no LLM
  4) segmentar em sentenças
  5) NLI (mDeBERTa v3 mnli/xnli) vs contextos -> entailed/neutral/contradiction
- Fact Score = #entailed / #sentenças
- Saídas:
  • eval/results/factscore.csv
  • eval/results/summary.json
  • eval/results/plot.png
