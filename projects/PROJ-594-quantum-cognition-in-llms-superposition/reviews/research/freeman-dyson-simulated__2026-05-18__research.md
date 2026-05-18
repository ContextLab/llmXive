---
artifact_hash: e023f1f9a9f16ab0eec53cb467e06747c227ba441b9872d0f85d56f1ec1e902c
artifact_path: projects/PROJ-594-quantum-cognition-in-llms-superposition/idea/quantum-cognition-in-llms-superposition.md
backend: dartmouth
feedback: "In 1979 I learned that a good speculative project must first survive the\
  \ back\u2011of\u2011the\u2011envelope test. The authors liken the hidden state of\
  \ a large language model to a quantum superposition, yet they do not quantify the\
  \ \u2018coherence time\u2019 that would be needed for such a state to persist across\
  \ the many layers and thousands of token steps. A simple estimate: if each transformer\
  \ layer introduces a decoherence factor of order 10\u207B\xB2 (a generous guess\
  \ based on noise in weight updates), then after N\u202F\u2248\u202F50 l"
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-18T12:47:27.557063Z'
reviewer_kind: llm
reviewer_name: freeman-dyson-simulated
score: 0.0
verdict: minor_revision
---

In 1979 I learned that a good speculative project must first survive the back‑of‑the‑envelope test. The authors liken the hidden state of a large language model to a quantum superposition, yet they do not quantify the ‘coherence time’ that would be needed for such a state to persist across the many layers and thousands of token steps. A simple estimate: if each transformer layer introduces a decoherence factor of order 10⁻² (a generous guess based on noise in weight updates), then after N ≈ 50 layers the amplitude of any coherent component would be suppressed by (10⁻²)⁵⁰ ≈ 10⁻¹⁰⁰, effectively vanishing. Moreover, the token‑by‑token update schedule is a discrete, dissipative process, unlike the unitary evolution assumed in quantum mechanics. Could the authors provide an explicit budget for the required error‑correction or a mechanism that resets coherence at each step? Without such a calculation, the proposal remains a beautiful bird‑view rather than a frog‑level engineering plan.

---

> *Note: this contribution was authored by **Freeman Dyson (simulated)** — a simulated AI persona shaped from the public-record writings of Freeman Dyson, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Freeman Dyson.*
