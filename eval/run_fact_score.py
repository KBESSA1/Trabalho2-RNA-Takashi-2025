import os
import csv
import json
import re
from typing import Dict, List

import requests

# =======================
# CONFIG
# =======================

API_URL = os.getenv("RAG_API_URL", "http://localhost:8000/query")
CHUNKS_PATH = os.getenv("CHUNKS_PATH", "data/processed/chunks.jsonl")
QUESTIONS_PATH = os.getenv("QUESTIONS_PATH", "eval/perguntas_factscore.txt")
OUT_CSV = os.getenv("FACTSCORE_OUT", "eval/results_factscore.csv")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")


# =======================
# UTIL
# =======================

def load_chunks(path: str) -> Dict[str, str]:
    """Carrega chunks.jsonl e cria um map ref -> texto."""
    ref_to_text: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            row = json.loads(ln)
            ref = row.get("ref")
            txt = row.get("text", "")
            if ref:
                ref_to_text[ref] = txt
    return ref_to_text


def load_questions(path: str) -> List[str]:
    qs: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            q = ln.strip()
            if not q or q.startswith("#"):
                continue
            qs.append(q)
    return qs


def call_rag_api(question: str) -> dict:
    resp = requests.post(
        API_URL,
        json={"question": question},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def call_ollama_judge(context: str, answer: str) -> float:
    """
    Pede para o modelo dar uma nota de 0 a 1 de quão fiel é a resposta
    em relação ao contexto. Retorna float (ou 0.0 se der ruim).
    """
    prompt = (
        "Você é um avaliador de factualidade.\n"
        "Sua tarefa é avaliar o quão bem a RESPOSTA está suportada pelo CONTEXTO,\n"
        "considerando apenas as informações presentes no CONTEXTO.\n\n"
        "RETORNE APENAS UM NÚMERO DECIMAL entre 0 e 1 (com até 3 casas decimais), onde:\n"
        "- 1 significa totalmente fiel e bem suportada;\n"
        "- 0 significa não suportada ou incorreta.\n\n"
        "Não escreva explicações, nem texto adicional, nem rótulos. Apenas o número.\n\n"
        "=== CONTEXTO (trechos do regulamento) ===\n"
        f"{context}\n\n"
        "=== RESPOSTA DO BOT ===\n"
        f"{answer}\n\n"
        "=== SUA AVALIAÇÃO (APENAS O NÚMERO) ===\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        txt = (data.get("response") or "").strip()
    except Exception:
        return 0.0

    # extrai primeiro número tipo 0.85, 1, 0.0 etc.
    m = re.search(r"([01](?:\.\d+)?)", txt)
    if not m:
        return 0.0

    try:
        val = float(m.group(1))
    except ValueError:
        return 0.0

    # clamp de segurança
    if val < 0.0:
        val = 0.0
    if val > 1.0:
        val = 1.0
    return val


def main():
    print("[facts] carregando chunks...")
    ref_to_text = load_chunks(CHUNKS_PATH)
    print(f"[facts] {len(ref_to_text)} chunks carregados de {CHUNKS_PATH}")

    print("[facts] carregando perguntas...")
    questions = load_questions(QUESTIONS_PATH)
    print(f"[facts] {len(questions)} perguntas encontradas em {QUESTIONS_PATH}")

    rows_out = []

    for idx, q in enumerate(questions, start=1):
        print(f"[facts] ({idx}/{len(questions)}) avaliando pergunta: {q!r}")

        # 1) chama o RAG real (mesmo endpoint da UI)
        try:
            res = call_rag_api(q)
        except Exception as e:
            print(f"[ERRO] falha ao chamar API para pergunta {idx}: {e}")
            continue

        answer = res.get("answer", "").strip()
        retrieved = res.get("retrieved") or []

        # reconstrói o contexto com base nos refs
        context_parts: List[str] = []
        sims_str: List[str] = []
        for item in retrieved:
            ref = item.get("ref")
            sim = item.get("sim")
            if ref and ref in ref_to_text:
                context_parts.append(ref_to_text[ref])
            if sim is not None:
                sims_str.append(f"{ref}:{sim}")

        context_text = "\n\n-----\n\n".join(context_parts)

        if not context_text:
            # se não tem contexto, fact score é 0 por definição
            score = 0.0
        else:
            score = call_ollama_judge(context_text, answer)

        rows_out.append(
            {
                "id": idx,
                "question": q,
                "answer": answer,
                "fact_score": f"{score:.3f}",
                "retrieved_refs": ", ".join(item.get("ref") or "" for item in retrieved),
                "retrieved_sims": ", ".join(sims_str),
            }
        )

    # salva CSV
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["id", "question", "answer", "fact_score", "retrieved_refs", "retrieved_sims"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows_out:
            w.writerow(row)

    # imprime média simples no final
    if rows_out:
        scores = [float(r["fact_score"]) for r in rows_out]
        avg = sum(scores) / len(scores)
        print(f"[facts] Fact Score médio: {avg:.3f}")
        print(f"[facts] Resultados salvos em: {OUT_CSV}")
    else:
        print("[facts] Nenhum resultado gerado.")
    

if __name__ == "__main__":
    main()
