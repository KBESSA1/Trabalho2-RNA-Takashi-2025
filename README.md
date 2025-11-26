# Trabalho 2 – RAG FACOM (Regulamento da Pós) – 2025

Implementação do Trabalho 2 (RAG) da disciplina do prof. Edson Takashi (FACOM/UFMS).

O sistema responde perguntas sobre o **Regulamento dos Cursos de Pós-graduação Stricto Sensu da UFMS (FACOM)** usando:

- ChromaDB como índice vetorial;
- `sentence-transformers/all-MiniLM-L6-v2` para embeddings;
- modelo generativo local via **Ollama** (ex.: `llama3.1:latest`);
- API FastAPI com interface web simples;
- script de avaliação de factualidade (Fact Score).

---

## 1. Arquitetura

Fluxo geral:

1. **Base de conhecimento**

   - `data/raw/REGULAMENTO.pdf`

2. **Pré-processamento / chunking**

   - `scripts/prepare_chunking.py` lê o PDF e produz:
     - `data/processed/chunks.jsonl`  
       (`id`, `source`, `ref` – por ex. `chunk_42` –, `chunk_id`, `text`)

3. **Indexação vetorial (ChromaDB)**

   - `scripts/seed_index.py`:
     - carrega `chunks.jsonl`;
     - gera embeddings com `all-MiniLM-L6-v2`;
     - grava no ChromaDB (`chroma_local/`, coleção `facom_regulamento_v1`).

4. **Recuperação + geração**

   - CLI: `scripts/ask.py`
   - API: `app/server.py` (endpoint `/query`)
   - Web: `web/index.html` (frontend bem simples)
   - Passos:
     1. gera embedding da pergunta;
     2. faz `query` no ChromaDB (top-k, com `SIM_THRESHOLD`);
     3. monta contexto com os trechos mais próximos;
     4. envia *contexto + pergunta* para o modelo via Ollama;
     5. devolve resposta textual, referenciando o regulamento.

   - Casos especiais:
     - pergunta ilegível (ex.: `jsahscvuoqnvcpqorhvou`)  
       → resposta: `Desculpe, não entendi o que você digitou, tente novamente.`
     - ausência de suporte no regulamento  
       → resposta padrão, encaminhando para a **Secretaria Acadêmica de PGCC**  
         (telefone, e-mail e horário de atendimento).

5. **Avaliação de factualidade (Fact Score)**

   - `eval/perguntas_factscore.txt`: 16 perguntas de teste (dentro e fora do regulamento).
   - `eval/run_fact_score.py`:
     - chama o `/query` para cada pergunta;
     - reconstrói o contexto a partir dos `ref` em `chunks.jsonl`;
     - pede a um modelo via Ollama uma nota de 0 a 1 (Fact Score).
   - `scripts/run_eval.sh`: atalho para rodar a avaliação.
   - `eval/results_factscore.csv`: tabela final (pergunta, resposta, fact_score, refs, similaridades).

   Execução atual: **Fact Score médio ≈ 0,48** (mistura de perguntas suportadas e perguntas fora de escopo).

---

## 2. Pré-requisitos

### 2.1. Ambiente Python

- Python 3.10+ (testado com 3.11)
- `pip`

(O projeto pode ser usado com Docker / Dev Container, mas não é obrigatório.)

### 2.2. Ollama

1. Instalar o Ollama no sistema.
2. Baixar o modelo (exemplo):

   ```bash
   ollama pull llama3.1


3. Garantir que o servidor Ollama está rodando.

Endpoints típicos:

* execução direta na máquina: `http://localhost:11434/api/generate`
* FastAPI dentro de container falando com Ollama no host: `http://host.docker.internal:11434/api/generate`

Esse valor é controlado pela variável de ambiente `OLLAMA_URL`.

---

## 3. Instalação (sem Docker)

Clonar o repositório:

```bash
git clone https://github.com/KBESSA1/Trabalho2-RNA-Takashi-2025.git
cd Trabalho2-RNA-Takashi-2025
```

Ambiente virtual (opcional):

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# ou
.venv\Scripts\activate       # Windows
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

---

## 4. Configuração de ambiente

Opcional: criar um `.env` na raiz a partir de `.env.example`.

Valores típicos:

```env
CHROMA_PATH=chroma_local
CHROMA_COLLECTION=facom_regulamento_v1

EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
TOP_K=5
SIM_THRESHOLD=0.45

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.1:latest
```

Em Dev Container / Docker, trocar `localhost` por `host.docker.internal` se o Ollama estiver no host.

---

## 5. Construção do índice

### 5.1. Chunking do PDF

Se ainda não houver `data/processed/chunks.jsonl`:

```bash
python scripts/prepare_chunking.py
```

Gera:

* `data/processed/chunks.jsonl`
* `data/processed/texto.txt`

### 5.2. Embeddings + ChromaDB

```bash
python scripts/seed_index.py
```

Saída esperada (exemplo):

```text
[emb] sentence-transformers/all-MiniLM-L6-v2 -> 74 docs
[OK] upsert 74 em 'facom_regulamento_v1' via PersistentClient (./chroma_local)
```

Cria/atualiza a coleção `facom_regulamento_v1` em `chroma_local/`.

---

## 6. Uso via linha de comando (`scripts/ask.py`)

Com o índice pronto:

```bash
# pergunta dentro do regulamento
python scripts/ask.py "Quais são os tipos de cursos de pós-graduação stricto sensu previstos nesse regulamento e quais as modalidades?"

# pergunta fora do regulamento
python scripts/ask.py "Qual é o prazo para entrega do TCC da graduação em Ciência da Computação?"
```

Comportamento:

* Perguntas com suporte → imprime a pergunta e trechos relevantes do regulamento.
* Perguntas sem suporte → mensagem de encaminhamento para a Secretaria de PGCC.
* Texto completamente ilegível → mensagem para o usuário tentar novamente.

---

## 7. API FastAPI e interface web

### 7.1. Servidor

Com o índice criado:

```bash
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=llama3.1:latest

uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

* API: `http://localhost:8000`
* Frontend: `web/index.html`, servido na raiz (`/`).

### 7.2. Navegador

Abrir:

```text
http://localhost:8000/
```

A página permite digitar uma pergunta, enviar e visualizar:

* resposta do bot;
* (opcional) referências aos chunks utilizados.

Exemplos:

* `O regulamento prevê Doutorado Profissional? Em que termos?`
* `Qual é o salário do Neymar?` (fora do escopo → mensagem de encaminhamento).

---

## 8. Avaliação de factualidade (Fact Score)

### 8.1. Arquivos

* `eval/perguntas_factscore.txt` – 16 perguntas.
* `eval/run_fact_score.py` – implementação do cálculo do Fact Score.
* `scripts/run_eval.sh` – shell script para rodar a avaliação.
* `eval/results_factscore.csv` – saída em CSV.

### 8.2. Execução

1. Manter o servidor FastAPI ativo:

   ```bash
   uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Em outro terminal:

   ```bash
   cd Trabalho2-RNA-Takashi-2025
   bash scripts/run_eval.sh
   ```

Saída típica:

```text
[eval] Rodando avaliação de Fact Score...
[facts] 74 chunks carregados de data/processed/chunks.jsonl
[facts] 16 perguntas encontradas em eval/perguntas_factscore.txt
...
[facts] Fact Score médio: 0.475
[facts] Resultados salvos em: eval/results_factscore.csv
```

O CSV contém, por linha: `id`, `question`, `answer`, `fact_score`, `retrieved_refs`, `retrieved_sims`.

---

## 9. Docker / Dev Container (opcional)

O repositório inclui:

* `.devcontainer/` – configuração de Dev Container (VS Code).
* `docker-compose.yml`
* `run_debug.sh`

Uso típico:

1. Abrir o projeto no VS Code.
2. “Reopen in Container”.
3. Dentro do container, seguir os mesmos passos:

   * `python scripts/prepare_chunking.py`
   * `python scripts/seed_index.py`
   * `uvicorn app.server:app ...`
   * `bash scripts/run_eval.sh`

Em cenários com Docker, ajustar `OLLAMA_URL` para falar com o Ollama do host.

---

## 10. Estrutura de pastas (resumo)

```text
.
├── .devcontainer/
├── app/
│   ├── server.py
│   └── ui/
├── data/
│   └── raw/
│       └── REGULAMENTO.pdf
├── eval/
│   ├── perguntas_factscore.txt
│   ├── results_factscore.csv
│   └── run_fact_score.py
├── scripts/
│   ├── ask.py
│   ├── prepare_chunking.py
│   ├── prepare_data.sh
│   ├── pull_models.sh
│   ├── run_eval.sh
│   └── seed_index.py
├── web/
│   └── index.html
├── chroma_local/         # gerado em runtime
├── requirements.txt
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 11. Autoria

Alunos:

* Rodrigo Luiz Chaves de Campos (KBESSA)
* Raphael Rodrigues Gonçalves

```
::contentReference[oaicite:0]{index=0}
```
