# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan validates the verifier’s alignment scores against 'human‑annotated feasibility scores' (FR‑001, FR‑003), yet these scores are *synthetically* generated via a deterministic antonym‑lookup procedure (see research.md §2). Because the same lexical resources and rule‑based logic underpin both the synthetic human scores and the symbolic constraint‑graph parser (which also uses an antonym lexicon to detect contradictions), the validation target is not independent of the predictor. This creates a circular/tautological validation: improvement in verifier scores may simply reflect alignment with the same rule‑based metric used to construct the graphs, not genuine model improvement.
- The statistical comparison (paired t‑test or Wilcoxon) tests the difference between baseline and graph‑augmented verifier scores *relative to the same synthetic human_score*. Since the human_score is deterministic and derived from the same rule‑based system that produces the graphs, the test does not assess whether the graph augmentation genuinely improves alignment with external reality; it merely measures consistency with an internally generated metric.
