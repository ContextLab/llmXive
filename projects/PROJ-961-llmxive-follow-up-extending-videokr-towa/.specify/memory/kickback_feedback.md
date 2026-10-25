# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan introduces FR-013 (new) – “Predicted Correctness Injection” – which has no corresponding Functional Requirement or Success Criterion in the specification. This constitutes an over‑reach; the plan should either remove this item or the spec should be updated to include a matching FR/SC.
- The plan generates a **synthetic, reproducible stand‑in for the VideoKR‑SFT dataset** (see lines 30‑38) and bases all analyses on this synthetic data. The research question targets the real VideoKR‑SFT dataset’s reasoning behavior; using synthetic data that only mimics schema does not guarantee the same hop‑count distribution or difficulty characteristics, making the dataset inappropriate for answering the intended question.
- The plan does not specify how the synthetic `correctness` labels are generated relative to `chain_length`. If correctness is derived deterministically from hop count (e.g., lower accuracy for higher hops), the downstream “reasoning cliff” detection becomes tautological: the predictor (hop count) and the outcome (correctness) are definitionally linked, guaranteeing a significant cliff. The validation would then be circular rather than an empirical test.
