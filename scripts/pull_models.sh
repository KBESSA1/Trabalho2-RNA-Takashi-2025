#!/usr/bin/env bash
set -euo pipefail
echo "[pull] requisitando modelo ao Ollama (host)"
curl -sS -X POST http://host.docker.internal:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name":"llama3.1"}' || { echo "[warn] falha ao falar com Ollama"; exit 1; }
echo
