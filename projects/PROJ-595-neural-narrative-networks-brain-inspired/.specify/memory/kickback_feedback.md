# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 8 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The power justification is vague; no effect‑size estimate, simulation, or reference is provided. For a permutation‑test RSA comparison across three ROIs, a formal power analysis (e.g., via Monte‑Carlo simulation) should be documented to ensure ≥ 80 % power for the expected effect size.
- The plan does not specify how inter‑subject variability will be handled. RSA should be computed per subject and then aggregated (e.g., mixed‑effects model) or a subject‑level permutation should be included to avoid confounding subject differences with model effects.
- FR-004 specifies a baseline *TinyLSTM (quantized transformer)*, but the plan implements a *quantized TinyBERT transformer* as the baseline (see Summary and Task T060/T037‑BASELINE). This does not satisfy the functional requirement for the baseline model type.
- The plan states a model size limit of ≤ 2 M parameters per model, yet the baseline uses a quantized TinyBERT (`bert-tiny`) which has ~4.4 M parameters, exceeding the declared constraint and likely violating the CPU‑only memory budget.
- The data model defines a ‘Narrative Representation (Pre‑training)’ entity (a .pt file of hidden‑state vectors from the SAE during ROCStories pre‑training). The plan’s Phase 2 tasks (e.g., T050.4) train the SAE on the ROCStories corpus but never specify saving or validating this pre‑training representation artifact, leaving the entity unused and violating Plan ↔ Data‑Model consistency.
- The permutation test uses an early‑stopping rule based on variance < 0.001 over the last 1,000 permutations. Early stopping can bias the null distribution and invalidate the p‑value unless a proper sequential testing correction is applied. Recommend either fixing the permutation count (e.g., always 2 000) or using a rigorously validated sequential Monte‑Carlo approach.
- RSA similarity is computed with Pearson correlation between model and neural RDMs. Pearson assumes linear relationships and can be sensitive to outliers; RSA literature often prefers rank‑based (Spearman) or distance‑based metrics. Consider offering Spearman or Kendall as alternatives or justify the choice.
- The baseline is described as a “standard transformer baseline (quantized TinyBERT)”. Earlier specifications (spec.md) refer to a “TinyLSTM (quantized transformer)”, which is inconsistent and may affect the scientific claim of comparing to a standard transformer architecture. Ensure the baseline is clearly defined and truly represents a standard transformer model.
