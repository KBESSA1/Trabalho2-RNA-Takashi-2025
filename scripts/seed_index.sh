#!/usr/bin/env bash
set -euo pipefail
# Apenas valida que o Chroma no host está acessível
URL="http://host.docker.internal:8001"
echo "[info] testando $URL ..."
curl -sS "$URL" | head -c 200 || true
echo
echo "[TODO] implementar criação de coleção e upsert de chunks"
