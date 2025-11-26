import os
import sys
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

# =======================
# CONFIG
# =======================

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_local")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "facom_regulamento_v1")

EMBEDDINGS_MODEL = os.getenv(
    "EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
TOP_K = int(os.getenv("TOP_K", "5"))

# similaridade mínima (0 a 1). Se ficar abaixo disso -> fallback
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.45"))

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
# UTIL
# =======================

def get_question() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    return input("Pergunta: ").strip()


def is_gibberish(text: str) -> bool:
    """
    Heurística simples para 'escrita ilegível':
    - uma única 'palavra' (sem espaços)
    - tamanho razoável (>= 8)
    - composta basicamente só por letras
    - proporção de vogais muito baixa
    """
    t = text.strip()
    if " " in t:
        return False  # tem mais de uma palavra, provavelmente não é puro ruído

    if len(t) < 8:
        return False

    if not t.isalpha():
        return False

    vowels = set("aeiouáéíóúâêôãõAEIOUÁÉÍÓÚÂÊÔÃÕ")
    num_vowels = sum(1 for c in t if c in vowels)
    ratio_vowels = num_vowels / len(t)

    # quase nenhuma vogal -> tem cara de 'jsahscvuqnv...'
    return ratio_vowels < 0.15


def build_answer(question: str, context_chunks: List[str]) -> str:
    header = (
        "Pergunta do usuário:\n"
        f"- {question}\n\n"
        "Trechos relevantes do Regulamento:\n\n"
    )
    body = "\n\n-----\n\n".join(context_chunks)
    return header + body


def main():
    question = get_question()
    if not question:
        print(FALLBACK_MESSAGE)
        return

    if is_gibberish(question):
        print(GIBBERISH_MESSAGE)
        return

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        coll = client.get_collection(CHROMA_COLLECTION)
    except Exception:
        print(FALLBACK_MESSAGE)
        return

    embedder = SentenceTransformer(EMBEDDINGS_MODEL)

    emb = embedder.encode([question], normalize_embeddings=True)[0].tolist()

    res = coll.query(
        query_embeddings=[emb],
        n_results=TOP_K,
        include=["documents", "distances"],
    )

    docs = res.get("documents") or []
    dists = res.get("distances") or []

    if not docs or not docs[0]:
        print(FALLBACK_MESSAGE)
        return

    documents = docs[0]
    distances = dists[0] if dists and dists[0] else None

    if distances is not None:
        sims = [1.0 - d for d in distances]
        best_sim = max(sims)
        if best_sim < SIM_THRESHOLD:
            print(FALLBACK_MESSAGE)
            return

    answer = build_answer(question, documents)
    print(answer)


if __name__ == "__main__":
    main()
