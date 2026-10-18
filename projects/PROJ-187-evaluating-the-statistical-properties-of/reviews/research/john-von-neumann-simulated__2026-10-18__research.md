---
action_items: []
artifact_hash: fc7cfd08e04afdc6398b88ef926ca647f3a3b888cfbc002bc51b9ab3787a2265
artifact_path: projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-evaluating-the-statistical-properties-of/spec.md
backend: dartmouth
feedback: 'The spec is on the whole disciplined, but the control-perturbation logic
  in FR-021/FR-022 does not establish what it claims. Permuting rows within each column
  preserves every marginal exactly while destroying all dependence structure; hence
  this dataset is a ground truth only for correlation fidelity (all pairs unfaithful)
  and, for marginals, is indistinguishable from the real hold-out (all columns faithful).
  It therefore cannot yield both false-positive and false-negative rates: against
  a refer'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-18T04:05:43.559637Z'
reviewer_kind: llm
reviewer_name: john-von-neumann-simulated
score: 0.0
verdict: minor_revision
---

The spec is on the whole disciplined, but the control-perturbation logic in FR-021/FR-022 does not establish what it claims. Permuting rows within each column preserves every marginal exactly while destroying all dependence structure; hence this dataset is a ground truth only for correlation fidelity (all pairs unfaithful) and, for marginals, is indistinguishable from the real hold-out (all columns faithful). It therefore cannot yield both false-positive and false-negative rates: against a reference whose labels are known only in one direction per metric family, one of the two error rates is undefined. FR-022 should be restricted to the correlation metrics, or a second control constructed (e.g., permuted marginals with preserved copula) to cover the other direction. Second, the categorical effect-size threshold in FR-020 is not an effect size: the chi-square statistic scales with sample size and degrees of freedom, so a fixed cutoff 'χ² ≤ χ²₀.₉₅' is either trivially violated or trivially satisfied depending on N and column cardinality; Cramér's V (or N-rescaled divergence) would be the commensurable quantity. Third, the assumption that 'power is assumed sufficient due to large N' cuts against the study: with N in the tens of thousands, KS and chi-square p-values will reject for negligible deviations, so the p-value leg of FR-020 will classify nearly everything unfaithful and the sensitivity sweep over {0.01, 0.05, 0.1} will show almost no variation — the effect-size leg is doing all the work, and the spec should say so. Finally, minor but real: FR-007 cites 'the control-perturbation dataset defined in FR-022' when the dataset is defined in FR-021, and FR-021 contains an unresolved placeholder ('randomly permuting [deferred] of rows') that leaves the perturbation fraction unspecified — a parameter that directly determines how unfaithful the control is, and hence the measured error rates.

---

> *Note: this contribution was authored by **John von Neumann (simulated)** — a simulated AI persona shaped from the public-record writings of John von Neumann, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual John von Neumann.*
