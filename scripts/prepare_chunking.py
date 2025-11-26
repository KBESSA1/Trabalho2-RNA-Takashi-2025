import os, json, re, sys, pathlib, statistics as st
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE","700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP","80"))
SRC = pathlib.Path("data/processed/texto.txt")
OUT = pathlib.Path("data/processed/chunks.jsonl")
QA  = pathlib.Path("data/processed/qa.json")
def clean(t:str)->str:
    t = t.replace("\x00",""); t = re.sub(r"[ \t]+"," ", t); t = re.sub(r"\n{3,}","\n\n", t); return t.strip()
def chunks(s, size, overlap):
    if overlap >= size: overlap = max(0, size//4)
    i=0; out=[]
    while i < len(s):
        c = s[i:i+size].strip()
        if c: out.append(c)
        if i+size >= len(s): break
        i += (size - overlap)
    return out
def main():
    if not SRC.exists():
        print("[ERRO] data/processed/texto.txt não encontrado; rode scripts/prepare_data.sh", file=sys.stderr); sys.exit(1)
    text = clean(SRC.read_text(encoding="utf-8", errors="ignore"))
    base = "\n\n".join([p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()])
    ch = chunks(base, CHUNK_SIZE, CHUNK_OVERLAP)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i,c in enumerate(ch):
            f.write(json.dumps({"id":f"reg_v1_{i:05d}","source":"REGULAMENTO.pdf","ref":f"chunk_{i}","chunk_id":i,"text":c}, ensure_ascii=False)+"\n")
    lens = [len(x) for x in ch]
    QA.write_text(json.dumps({"n_chunks":len(ch),"len_chars_mean":float(st.mean(lens)) if lens else 0,
                              "len_chars_p95": float(sorted(lens)[int(0.95*len(lens))-1]) if lens else 0,
                              "chunk_size":CHUNK_SIZE,"chunk_overlap":CHUNK_OVERLAP}, ensure_ascii=False, indent=2))
    print(f"[OK] {len(ch)} chunks => {OUT}")
if __name__=="__main__": main()
