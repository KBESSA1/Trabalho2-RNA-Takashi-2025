.PHONY: prepare chunk index ask reset-local smoke

prepare: ; ./scripts/prepare_data.sh
chunk:   ; python scripts/prepare_chunking.py
index:   ; python scripts/seed_index.py
ask:     ; @echo 'uso: make ask q="sua pergunta"'; \
          [ -z "$(q)" ] || python scripts/ask.py "$(q)"
reset-local:
	@echo "[wipe] removendo ./chroma_local (índice local)"
	rm -rf ./chroma_local
smoke:
	@echo ">>> Smoke test: prazos de defesa"; \
	python scripts/ask.py "Quais são os prazos para defesa?" || exit 1
