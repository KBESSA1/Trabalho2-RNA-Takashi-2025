import os
from typing import List, Optional, Any, Dict

import chromadb
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests

# =======================
# CONFIG
# =======================

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_local")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "facom_regulamento_v1")

EMBEDDINGS_MODEL = os.getenv(
    "EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
TOP_K = int(os.getenv("TOP_K", "5"))

SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.45"))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

FALLBACK_MESSAGE = (
    "Desculpe, baseado no regulamento, não consigo informar com precisão. "
    "Favor, entre em contato com a Secretaria Academica de PGCC:\n\n"
    "Telefone: (67) 3345-7456 / E-mail: ppg.facom@ufms.br\n"
    "Endereço: Avenida Costa e Silva, s/n; Bairro Universitário; Cep:79070-900\n\n"
    "Horário de Atendimento:\n\n"
    "Secretaria de Graduação: Segunda à sexta-feira, 8h às 12h / 13h às 17h\n"
    "Secretaria de Pós-graduação: Segunda à sexta-feira, 8h às 12h / 13h às 17h"
)

GIBBERISH_MESSAGE = "Desculpe, não entendi o que você digitou, tente novamente."

# =======================
# INIT CHROMA + EMBEDDER
# =======================

_client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    _collection = _client.get_collection(CHROMA_COLLECTION)
except Exception:
    _collection = None

_embedder = SentenceTransformer(EMBEDDINGS_MODEL)

# =======================
# FASTAPI APP
# =======================

app = FastAPI(title="FACOM Bot — Regulamento")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class RetrievedItem(BaseModel):
    ref: Optional[str] = None
    sim: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    retrieved: List[RetrievedItem] = []


def _is_gibberish(text: str) -> bool:
    """
    Mesma heurística do CLI:
    - uma palavra só
    - comprida
    - só letras
    - quase sem vogal
    """
    t = text.strip()
    if " " in t:
        return False

    if len(t) < 8:
        return False

    if not t.isalpha():
        return False

    vowels = set("aeiouáéíóúâêôãõAEIOUÁÉÍÓÚÂÊÔÃÕ")
    num_vowels = sum(1 for c in t if c in vowels)
    ratio_vowels = num_vowels / len(t)

    return ratio_vowels < 0.15


def _rag_search(question: str) -> Dict[str, Any]:
    if not question or _collection is None:
        return {"docs": [], "sims": [], "metas": []}

    emb = _embedder.encode([question], normalize_embeddings=True)[0].tolist()

    res = _collection.query(
        query_embeddings=[emb],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    docs = res.get("documents") or []
    dists = res.get("distances") or []
    metas = res.get("metadatas") or []

    if not docs or not docs[0]:
        return {"docs": [], "sims": [], "metas": []}

    documents = docs[0]
    distances = dists[0] if dists and dists[0] else []
    metadatas = metas[0] if metas and metas[0] else [{} for _ in documents]

    if distances:
        sims = [1.0 - d for d in distances]
        best_sim = max(sims)
        if best_sim < SIM_THRESHOLD:
            return {"docs": [], "sims": [], "metas": []}
    else:
        sims = [None] * len(documents)

    return {"docs": documents, "sims": sims, "metas": metadatas}


def _build_extractive_answer(question: str, docs: List[str]) -> str:
    header = (
        "Pergunta do usuário:\n"
        f"- {question}\n\n"
        "Trechos relevantes do Regulamento:\n\n"
    )
    body = "\n\n-----\n\n".join(docs)
    return header + body


def _build_llm_prompt(question: str, docs: List[str]) -> str:
    contexto = "\n\n-----\n\n".join(docs)
    prompt = (
        "Você é um assistente da FACOM/UFMS.\n"
        "Você deve responder em português brasileiro, de forma clara e educada, "
        "APENAS com base no regulamento abaixo.\n\n"
        "REGRAS:\n"
        "1. Responda em 2 a 4 frases completas, sem começar apenas com 'Sim.' ou 'Não.'.\n"
        "2. Deixe explícito se o regulamento PERMITE, PROÍBE ou NÃO MENCIONA o que foi perguntado.\n"
        "3. Quando possível, explique de forma resumida o que o regulamento determina.\n"
        "4. Ao final, cite os artigos ou trechos que embasam a resposta, no formato: "
        "'Baseado nos Art. X, Y, ...'.\n"
        "5. NÃO invente informações fora do texto. Se os trechos abaixo não forem suficientes "
        "para responder com segurança, responda exatamente o seguinte texto:\n"
        "'Desculpe, baseado no regulamento, não consigo informar com precisão. "
        "Favor, entre em contato com a Secretaria Academica de PGCC:\n\n"
        "Telefone: (67) 3345-7456 / E-mail: ppg.facom@ufms.br\n"
        "Endereço: Avenida Costa e Silva, s/n; Bairro Universitário; Cep:79070-900\n\n"
        "Horário de Atendimento:\n\n"
        "Secretaria de Graduação: Segunda à sexta-feira, 8h às 12h / 13h às 17h\n"
        "Secretaria de Pós-graduação: Segunda à sexta-feira, 8h às 12h / 13h às 17h'.\n\n"
        "=== REGULAMENTO (trechos selecionados) ===\n"
        f"{contexto}\n\n"
        "=== PERGUNTA DO USUÁRIO ===\n"
        f"{question}\n\n"
        "=== SUA RESPOSTA ===\n"
    )
    return prompt


def _call_ollama(prompt: str) -> Optional[str]:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        txt = data.get("response") or str(data)
        return txt.strip()
    except Exception:
        return None


@app.get("/")
def root():
    return FileResponse("web/index.html")


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    q = req.question.strip()
    if not q:
        return QueryResponse(answer=FALLBACK_MESSAGE, retrieved=[])

    if _is_gibberish(q):
        return QueryResponse(answer=GIBBERISH_MESSAGE, retrieved=[])

    rag = _rag_search(q)
    docs = rag.get("docs") or []
    sims = rag.get("sims") or []
    metas = rag.get("metas") or []

    if not docs:
        return QueryResponse(answer=FALLBACK_MESSAGE, retrieved=[])

    prompt = _build_llm_prompt(q, docs)
    llm_answer = _call_ollama(prompt)

    if llm_answer:
        answer = llm_answer
    else:
        answer = _build_extractive_answer(q, docs)

    retrieved: List[RetrievedItem] = []
    for meta, sim in zip(metas, sims):
        ref = None
        if isinstance(meta, dict):
            ref = meta.get("ref")
        sim_round = float(f"{sim:.3f}") if isinstance(sim, (float, int)) else None
        retrieved.append(RetrievedItem(ref=ref, sim=sim_round))

    return QueryResponse(answer=answer, retrieved=retrieved)
