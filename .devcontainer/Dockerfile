FROM mcr.microsoft.com/devcontainers/python:3.11

# utilitários úteis para ingestão (PDF/OCR) e análise
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-por jq && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/rag-facom
