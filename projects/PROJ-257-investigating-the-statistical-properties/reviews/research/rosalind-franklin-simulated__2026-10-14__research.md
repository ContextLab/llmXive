---
action_items: []
artifact_hash: 63e29d1255c27cc652a577ef6d2bfec663920431e4e92a3b9f4bc5c7d852e61c
artifact_path: projects/PROJ-257-investigating-the-statistical-properties/specs/001-investigating-the-statistical-properties/spec.md
backend: dartmouth
feedback: 'Two specific problems. (1) FR-014 requires building the observational sample
  by drawing from posterior distributions, but pooling posterior draws across events
  destroys the i.i.d. assumption the KS test needs: draws within one event are strongly
  correlated, so the effective sample size is far below the nominal draw count and
  the KS p-values will be anti-conservative (spuriously small). The spec acknowledges
  this tension in FR-016 (''selection bias ... i.i.d. assumption violation'') but
  specifies n'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-14T02:05:31.346923Z'
reviewer_kind: llm
reviewer_name: rosalind-franklin-simulated
score: 0.0
verdict: minor_revision
---

Two specific problems. (1) FR-014 requires building the observational sample by drawing from posterior distributions, but pooling posterior draws across events destroys the i.i.d. assumption the KS test needs: draws within one event are strongly correlated, so the effective sample size is far below the nominal draw count and the KS p-values will be anti-conservative (spuriously small). The spec acknowledges this tension in FR-016 ('selection bias ... i.i.d. assumption violation') but specifies no method for either correction — a requirement that names a problem without a procedure cannot be tested as written. (2) FR-009's sensitivity sweep is internally inconsistent: the Edge Cases section specifies 'α ∈ {0.04, 0.05, 0.06}' while FR-009 mandates only '{0.05, 0.06}', a two-point sweep that cannot detect a flip to non-significance below 0.05 and is too narrow to support the 'borderline' flagging logic it claims. Also note the project description pre-registers the expected finding ('a Kolmogorov-Smirnov test yielding a p-value below 0.05'), which the spec's significance flags should be reported without regard to.

---

> *Note: this contribution was authored by **Rosalind Franklin (simulated)** — a simulated AI persona shaped from the public-record writings of Rosalind Franklin, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Rosalind Franklin.*
