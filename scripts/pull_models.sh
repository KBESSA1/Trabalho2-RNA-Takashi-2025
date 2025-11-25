#!/usr/bin/env bash
set -euo pipefail
# Baixa o modelo padrão para respostas
curl -sS -X POST http://host.docker.internal:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name":"llama3.1"}'
echo
