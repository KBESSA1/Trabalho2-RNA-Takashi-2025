# Guardrails
- Responder apenas com base no contexto recuperado.
- Se não houver suporte: "não encontrado no regulamento".
- Limite de similaridade (cosine) para incluir trecho no prompt: τ = 0.25 (ajustável).
- Limite de tamanho do prompt: ~3k tokens (ajustar ao LLM).
- Sempre citar [Fonte: {source}, {ref}, chunk {chunk_id}].
