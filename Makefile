.PHONY: up down pull prepare seed logs

up:
	@echo "[compose] subindo serviços no HOST"
	@echo " -> rode no HOST: docker compose up -d"

down:
	@echo "[compose] derrubando serviços no HOST"
	@echo " -> rode no HOST: docker compose down"

pull:
	./scripts/pull_models.sh

prepare:
	./scripts/prepare_data.sh

seed:
	./scripts/seed_index.sh

logs:
	@echo "[hint] no HOST: docker compose logs -f --tail=200"
