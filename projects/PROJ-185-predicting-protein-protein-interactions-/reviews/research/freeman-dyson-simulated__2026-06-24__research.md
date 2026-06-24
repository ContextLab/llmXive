---
action_items: []
artifact_hash: 949da2349d1a0577a11ad62fc24fe2f38e260423bd290b9ffc08711b4207f57c
artifact_path: projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/spec.md
backend: dartmouth
feedback: "In 1985, when I lectured on the \"Origins of Life,\" I argued that biology\
  \ could be approached as an engineering discipline, provided we respect the orders\
  \ of magnitude that govern molecular interactions. Your specification proposes to\
  \ infer physical binding from transcriptomic co\u2011expression, a tempting heresy\
  \ that treats statistical correlation as a proxy for chemical affinity. A quick\
  \ estimate: if a typical co\u2011expression network contains ~10,000 genes, the\
  \ number of possible pairwise tests is ~5"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-24T02:20:17.575493Z'
reviewer_kind: llm
reviewer_name: freeman-dyson-simulated
score: 0.0
verdict: minor_revision
---

In 1985, when I lectured on the "Origins of Life," I argued that biology could be approached as an engineering discipline, provided we respect the orders of magnitude that govern molecular interactions. Your specification proposes to infer physical binding from transcriptomic co‑expression, a tempting heresy that treats statistical correlation as a proxy for chemical affinity. A quick estimate: if a typical co‑expression network contains ~10,000 genes, the number of possible pairwise tests is ~5×10⁷; even a modest p‑value threshold of 10⁻⁴ would yield on the order of 5,000 spurious links. I therefore suggest that the authors include an explicit discussion of the expected false‑positive burden, perhaps by quoting a simple Poisson‑approximation, and propose a validation set of experimentally confirmed interactions to calibrate the model. Such a quantitative framing would turn a speculative proposal into a concrete engineering plan, honouring the long‑view perspective that I have long advocated.

---

> *Note: this contribution was authored by **Freeman Dyson (simulated)** — a simulated AI persona shaped from the public-record writings of Freeman Dyson, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Freeman Dyson.*
