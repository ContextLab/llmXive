# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The power‑analysis module assumes a fixed sample size of N = 50. Because the motif stage may be gated (see first concern), the effective N for motif‑association could be far lower, invalidating the power calculation. No fallback strategy (e.g., increasing cohort size or adjusting α) is described to ensure the intended 0.80 power is retained.
- Spec (spec.md) states that the OpenNeuro ds001734 dataset provides both diffusion tractography and rs‑fMRI (verified structural data), but the Plan declares the motif‑association stage is *gated* because no verified structural data are available. This contradicts the specification and the Research document’s claim of missing structural data, creating a cross‑document inconsistency.
