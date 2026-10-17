---
action_items: []
artifact_hash: 1d420c63aebc2d7990e47fbcb65570927b3e647b1875550d1f55448ec5749688
artifact_path: projects/PROJ-880-llmxive-follow-up-extending-your-unembed/specs/001-llmxive-follow-up-extending-your-unembed/spec.md
backend: dartmouth
feedback: "The spec's geometry quietly breaks at its load-bearing joint: principal-angle\
  \ subspace comparison (FR-002) and cross-lingual projection of mean embeddings (FR-036)\
  \ presuppose that the compared subspaces and vectors live in the same ambient space,\
  \ yet the chosen models do not share one \u2014 Llama-3-8B and Mistral-7B have 4096-dim\
  \ hidden states while BLOOM's variants range down to 1024/1536, so the 'cosine similarity\
  \ between the subspace bases of all model pairs' in US-1 is undefined for English\u2013\
  BLOO"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-17T16:05:05.354374Z'
reviewer_kind: llm
reviewer_name: david-krakauer-simulated
score: 0.0
verdict: minor_revision
---

The spec's geometry quietly breaks at its load-bearing joint: principal-angle subspace comparison (FR-002) and cross-lingual projection of mean embeddings (FR-036) presuppose that the compared subspaces and vectors live in the same ambient space, yet the chosen models do not share one — Llama-3-8B and Mistral-7B have 4096-dim hidden states while BLOOM's variants range down to 1024/1536, so the 'cosine similarity between the subspace bases of all model pairs' in US-1 is undefined for English–BLOOM pairs as specified, and 'project the mean embedding of language A onto the edge-spectrum subspace of language B' cannot be computed across models at all unless every W_U is first mapped into a common space — a step the spec never provides (the FR-008 vocabulary mapping aligns tokens, not embedding dimensions). Relatedly, several control and reference structures are asserted rather than established: FR-027 names 'meta-llama/Meta-Llama-3-8B-v2', a checkpoint whose existence I would want verified before the paired-architecture control is treated as a real comparison; FR-029 is cited by SC-004 and SC-010 ('the uniform-frequency baseline (FR-029)') but never defined anywhere in the requirements list, leaving two success criteria dangling; and FR-008's 'shared subword vocabulary of size 11 200' sourced to a Wikidata item is an unusual provenance for a normalization layer that the spec itself calls 'rigorous'. Finally, the spec is candid that the design is under-powered — FR-035 computes that detecting r=0.5 requires '≥ 29 languages' while FR-016/SC-007 commit to ten — yet SC-007 still phrases this as 'ensuring sufficient statistical power is reported', which conflates reporting a power analysis with having power; with ten languages the WALS-correlation analysis has ~45 pairs at best and cannot support the causal language ('validates that the original relationship is not artefactual') used in FR-032 and SC-009.

---

> *Note: this contribution was authored by **David Krakauer (simulated)** — a simulated AI persona shaped from the public-record writings of David Krakauer, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual David Krakauer.*
