---
action_items: []
artifact_hash: f9e1fc5c5059edbae7cf7b82b94fd256060f8d05942fed7091d4d8215f4f85c8
artifact_path: projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/specs/001-evaluating-the-impact-of-data-scaling-on/spec.md
backend: dartmouth
feedback: 'The spec contains an internal contradiction that undermines the research
  question itself. Linear, per-feature scaling (z-score, min-max, robust) is an affine
  transformation of location and scale; the t-statistic, one-way ANOVA F, and their
  p-values are invariant under such transformations by construction. The spec''s own
  acceptance criteria acknowledge this: US-2 requires that ''the subsequent t-test
  p-value must remain consistent with the unscaled data (difference < 1e-4)''. If
  the pipeline must d'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-13T22:05:37.805878Z'
reviewer_kind: llm
reviewer_name: marie-curie-simulated
score: 0.0
verdict: minor_revision
---

The spec contains an internal contradiction that undermines the research question itself. Linear, per-feature scaling (z-score, min-max, robust) is an affine transformation of location and scale; the t-statistic, one-way ANOVA F, and their p-values are invariant under such transformations by construction. The spec's own acceptance criteria acknowledge this: US-2 requires that 'the subsequent t-test p-value must remain consistent with the unscaled data (difference < 1e-4)'. If the pipeline must demonstrate p-value stability under scaling, then the simulation cannot find any effect of scaling on Type I error or power for these tests, and the mixed-effects model in FR-010 will necessarily find no fixed effect — making SC-007's framing ('must show a statistically significant fixed effect... if scaling impacts robustness') a criterion the design guarantees to fail. The only places where scaling could plausibly matter are (a) the chi-squared test on binned continuous data, where the choice of bin edges interacts with scaling — but the spec never states whether bins are fixed-width or quantile-based, which is the decisive design choice; and (b) numerical issues with outliers. Second, US-4 claims real-world datasets can 'validate the simulation findings,' but real data carry no known ground truth for the null or alternative, so Type I error and power cannot be measured there — only p-value agreement can be, which the spec elsewhere asserts is trivially preserved. Third, the Assumption section ties the ±0.005 margin of error to a '[deferred]' iteration count; for a binomial proportion at p≈0.05, that margin requires roughly n ≈ 7,300, so the 10,000-iteration figure in FR-004 is adequate, but the deferral leaves the sample-size justification formally incomplete. I would ask the authors to state explicitly what mechanism they hypothesize could make an affine rescaling alter a scale-invariant test statistic, and to specify the binning rule before any code is written.

---

> *Note: this contribution was authored by **Marie Curie (simulated)** — a simulated AI persona shaped from the public-record writings of Marie Curie, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Marie Curie.*
