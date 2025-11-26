#!/usr/bin/env bash
set -euo pipefail
URL="http://host.docker.internal:8001"
echo "[seed] testando $URL ..."
curl -sS "$URL" | head -c 200 || true
echo
echo "[TODO] criar coleção e upsert de chunks (ChromaDB)"
