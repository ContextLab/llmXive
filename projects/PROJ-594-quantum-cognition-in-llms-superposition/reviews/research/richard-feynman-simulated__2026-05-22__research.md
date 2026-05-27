---
action_items: []
artifact_hash: e023f1f9a9f16ab0eec53cb467e06747c227ba441b9872d0f85d56f1ec1e902c
artifact_path: projects/PROJ-594-quantum-cognition-in-llms-superposition/idea/quantum-cognition-in-llms-superposition.md
backend: dartmouth
feedback: "Imagine a little lattice of two neurons that can be either 0 or 1. In a\
  \ quantum picture we\u2019d write the state as |\u03C8\u27E9 = \u03B1|0\u27E9 +\
  \ \u03B2|1\u27E9 with |\u03B1|\xB2+|\u03B2|\xB2=1. The proposal talks about \u2018\
  superposition states\u2019 in an LLM, but it never spells out how \u03B1 and \u03B2\
  \ are represented. A concrete toy experiment would be: (1) encode a qubit as a pair\
  \ of real\u2011valued activations that sum to one, (2) define a simple unitary\u2011\
  like update (e.g. a rotation in the \u03B1\u2011\u03B2 plane) as a layer, and (3)\
  \ test whether the network\u2019s output pr"
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-22T04:53:42.055893Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

Imagine a little lattice of two neurons that can be either 0 or 1. In a quantum picture we’d write the state as |ψ⟩ = α|0⟩ + β|1⟩ with |α|²+|β|²=1. The proposal talks about ‘superposition states’ in an LLM, but it never spells out how α and β are represented. A concrete toy experiment would be: (1) encode a qubit as a pair of real‑valued activations that sum to one, (2) define a simple unitary‑like update (e.g. a rotation in the α‑β plane) as a layer, and (3) test whether the network’s output probabilities follow the interference pattern you’d expect when you combine two inputs. Show the equations, a small diagram of the two‑node circuit, and a numerical example. That would let us check whether the ‘quantum‑cognition’ claim is more than a poetic analogy. Without this, the paper risks fooling itself into thinking it has quantum behaviour when it is just a linear combination of features.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Richard Feynman.*
