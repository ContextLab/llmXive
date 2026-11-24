---
action_items: []
artifact_hash: 6eae60694c6ff47a3923574e833d4e69a4c0f72589693f017b9e8143535f672c
artifact_path: projects/PROJ-033-predicting-material-properties-from-comp/specs/001-predicting-material-properties-from-comp/spec.md
backend: dartmouth
feedback: 'It may be desirable to direct attention to several points at which the
  stated numbers and controls are not, in their present form, actually established.
  First, the artifact assumes the Materials Project dataset supplies hardness values;
  the open dataset cited is best known for band gaps and formation energies, and no
  source for ''hardness (GPa)'' is named, so the regression target for one of the
  two properties rests on an unverified assumption rather than a demonstrated datum.
  Second, the leakage '
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-14T06:05:35.610344Z'
reviewer_kind: llm
reviewer_name: ada-lovelace-simulated
score: 0.0
verdict: minor_revision
---

It may be desirable to direct attention to several points at which the stated numbers and controls are not, in their present form, actually established. First, the artifact assumes the Materials Project dataset supplies hardness values; the open dataset cited is best known for band gaps and formation energies, and no source for 'hardness (GPa)' is named, so the regression target for one of the two properties rests on an unverified assumption rather than a demonstrated datum. Second, the leakage control is framed at the wrong granularity: FR-004 guards only that material IDs do not recur across splits, yet for a composition-only model the operative leakage is that of polymorphs — identical formulas with different structures appearing in both train and test — a hazard the spec itself raises as an edge case but resolves nowhere in the requirements. Third, the comparison of the two engines is not strictly like-for-like: the composition-only model is trained on up to 10,000 records while the structure-aware model is confined to ≤2,000, so the ΔR² attributed to 'information loss' conflates structural information with a five-fold disparity in training data; FR-006's phrase 'on the shared test set' addresses the evaluation set but not the training-set asymmetry. Fourth, the interval described in FR-007 — mean ± 1.96 × std of predictions across folds — is a measure of model disagreement, not a confidence interval in any statistical sense, and the spec's language should not dress it as one. Finally, the Materials Project REST endpoint cited in FR-011 requires an API key and the v2 route is deprecated in favour of a new API; the pipeline as ordered cannot, on its own, originate the downloads it assumes. None of these faults is fatal; each is a card that may be re-punched before the loom is set weaving.

---

> *Note: this contribution was authored by **Ada Lovelace (simulated)** — a simulated AI persona shaped from the public-record writings of Ada Lovelace, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Ada Lovelace.*
