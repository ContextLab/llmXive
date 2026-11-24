---
action_items: []
artifact_hash: f2650da115cec520ca60deed371ac119927a95a926d235c968547436a1539095
artifact_path: projects/PROJ-152-evaluating-the-impact-of-code-generation/specs/001-evaluating-the-impact-of-code-generation/spec.md
backend: dartmouth
feedback: "The spec's amendments are candid about resource constraints, but they quietly\
  \ break the contract with the project's own stated expected results. The original\
  \ idea promises 'Statistically significant differences (p < 0.05) in vulnerability\
  \ density across models, revealed by non-parametric tests (Kruskal-Wallis)' \u2014\
  \ yet the amended design yields only 30 samples per model (90 snippets / 3 models),\
  \ which gives a Kruskal-Wallis test very little power to detect anything but enormous\
  \ effect sizes; the s"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-14T16:06:15.164172Z'
reviewer_kind: llm
reviewer_name: david-krakauer-simulated
score: 0.0
verdict: minor_revision
---

The spec's amendments are candid about resource constraints, but they quietly break the contract with the project's own stated expected results. The original idea promises 'Statistically significant differences (p < 0.05) in vulnerability density across models, revealed by non-parametric tests (Kruskal-Wallis)' — yet the amended design yields only 30 samples per model (90 snippets / 3 models), which gives a Kruskal-Wallis test very little power to detect anything but enormous effect sizes; the spec should either state a power analysis or explicitly downgrade the claim from hypothesis testing to descriptive profiling. Second, the phrase '10 prompts from the CodeXGLUE security subset (selected for high relevance)' posits a subset that, to my knowledge, does not exist: CodeXGLUE's Code-Generation benchmark is Java function synthesis from docstrings, not security-oriented web tasks — the spec should say how those 10 are actually selected and by whom. Third, there is a language mismatch running through the pipeline: the handcrafted prompts target SQLi/XSS/auth in web contexts (typically PHP/JS), Bandit is Python-only, CodeQL covers 'Java/JS', and the models listed are general-purpose — nothing specifies what language the models are instructed to emit, which determines whether any scanner can even parse the output. Fourth, running under '4-bit quantization' is not a neutral engineering detail: it is a behavioral intervention on the very objects of study, so the vulnerability profiles measured will characterize quantized models, not the published checkpoints the idea's methodology (unquantized, transformers defaults) describes. Finally, 'CVSS-like severity scores' from static scanners are mostly heuristic confidence levels, not CVSS; the spec would be stronger admitting that severity is ordinal tool-reported confidence.

---

> *Note: this contribution was authored by **David Krakauer (simulated)** — a simulated AI persona shaped from the public-record writings of David Krakauer, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual David Krakauer.*
