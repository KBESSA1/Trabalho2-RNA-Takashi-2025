import os, json
import chromadb
from sentence_transformers import SentenceTransformer

NAME = os.getenv("CHROMA_COLLECTION","facom_regulamento_v1")
EMB  = os.getenv("EMBEDDINGS_MODEL","sentence-transformers/all-MiniLM-L6-v2")

rows=[]
with open("data/processed/chunks.jsonl","r",encoding="utf-8") as f:
    for ln in f:
        ln=ln.strip()
        if ln: rows.append(json.loads(ln))
if not rows:
    raise SystemExit("[ERRO] sem chunks; rode scripts/prepare_chunking.py")

docs=[r["text"] for r in rows]
ids=[r["id"] for r in rows]
metas=[{"source":r["source"],"ref":r["ref"],"chunk_id":r["chunk_id"]} for r in rows]

print(f"[emb] {EMB} -> {len(docs)} docs")
model = SentenceTransformer(EMB)
embs = model.encode(docs, batch_size=64, show_progress_bar=True, normalize_embeddings=True).tolist()

client = chromadb.PersistentClient(path="chroma_local")
# recria sempre a coleção do zero p/ evitar configs antigas
try:
    client.delete_collection(NAME)
except Exception:
    pass
coll = client.create_collection(name=NAME, metadata={"hnsw:space":"cosine"})

coll.add(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
print(f"[OK] upsert {len(ids)} em '{NAME}' via PersistentClient (./chroma_local)")
