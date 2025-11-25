# Index Schema (ChromaDB)
- collection: CHROMA_COLLECTION (env)
- id: hash( fonte + ref + offset )
- document: texto do chunk
- metadata:
  - source: "REGULAMENTO.pdf"
  - ref: artigo/seção/página estimada (se disponível)
  - chunk_id: inteiro sequencial
  - span: [start_char, end_char] no texto base
  - tokens: contagem aproximada
