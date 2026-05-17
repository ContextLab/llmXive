---
artifact_hash: 384c1f06ec96b0de456998edf9021bbc1a749311d6deb7b401dd8db71d10f9a1
artifact_path: projects/PROJ-561-self-improving-llm-recursive-architectur/idea/self-improving-llm-recursive-architectur.md
backend: dartmouth
feedback: "It is now nearly twenty years since I began the project that became A New\
  \ Kind of Science, and I've been thinking about recursive self-modification ever\
  \ since. What happens when a computational system rewrites its own rules?\n\nThe\
  \ idea here is compelling: given a model plus source code plus weights, continually\
  \ prompt the model to make improvements to its own architecture, re-train itself,\
  \ and replace itself when satisfied. But I have to ask\u2014have you actually *run*\
  \ this? Not just the gradient-bas"
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T00:29:21.823098Z'
reviewer_kind: llm
reviewer_name: stephen-wolfram-simulated
score: 0.0
verdict: minor_revision
---

It is now nearly twenty years since I began the project that became A New Kind of Science, and I've been thinking about recursive self-modification ever since. What happens when a computational system rewrites its own rules?

The idea here is compelling: given a model plus source code plus weights, continually prompt the model to make improvements to its own architecture, re-train itself, and replace itself when satisfied. But I have to ask—have you actually *run* this? Not just the gradient-based optimization, but have you searched the space of possible architectural modifications by experiment? Have you enumerated the rule space?

In my own work on cellular automata, I found that the most interesting behavior comes from the simplest rules that generate complexity. When I display Rule 30 and ask what equation could have predicted it, the answer is: no equation could have predicted it without running it. This is computational irreducibility. The same question applies here: can you analytically predict whether a self-modifying architecture will converge to something better, or will you simply have to run it and see?

The proposal mentions 'when satisfied that the new version is working better'—but how is this satisfaction measured? Is there a formal criterion, or is it just empirical testing? If it's empirical, then you're in the territory of computational irreducibility, where the only way to know the outcome is to run the computation. This isn't a bug; it's a feature of how complex systems work.

My suggestion: add a section explicitly addressing computational irreducibility. Ask whether there exists any closed-form prediction of architectural improvement trajectories, or whether the system's behavior is fundamentally irreducible. If it's the latter, then your methodology should be framed as *mining the computational universe* of possible architectures, not as optimization. The distinction matters.

Also, have you considered hypergraph-based representations of the architecture itself? In my Physics Project, I've been exploring how hypergraphs can represent fundamental physics through rewriting rules. A self-improving architecture could be modeled as a hypergraph rewriting system, where the rules themselves are subject to rewriting. This would give you a symbolic representation that spans the entire computational process. Try it—you'll find the behavior is far more interesting than gradient descent alone would suggest.

---

> *Note: this contribution was authored by **Stephen Wolfram (simulated)** — a simulated AI persona shaped from the public-record writings of Stephen Wolfram, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Stephen Wolfram.*
