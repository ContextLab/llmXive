# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 11 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'science'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 specifies subsampling to '[deferred] reads per sample' while Assumptions section states '10,000 reads per sample'. The placeholder in the requirement is not explicitly resolved, creating internal inconsistency between FR-003 and Assumptions.
- Assumptions section states 'The subsampling depth of [deferred] reads per sample is applied uniformly' while Constitution Principle VI and FR-010 reference concrete 10,000 reads. The placeholder in Assumptions is unresolved, leading to conflicting specifications.
- Edge Cases still mention '[deferred] reads per sample' for 'Insufficient Reads' scenario, which conflicts with the now-specified 10,000-read subsampling depth in FR-010 and Constitution Principle VI.
- FR-005 defines model input as diversity metrics, contradicting the idea's emphasis on baseline taxa abundances for prediction. This discrepancy makes the FR less verifiable against the core research question.
- The feature branch name is still the placeholder '[###-feature-name]'. A valid branch name is required for reproducibility and traceability.
- Edge Cases still mention '[deferred] reads per sample' for the ‘Insufficient Reads’ scenario, which conflicts with the now-specified 10,000-read subsampling depth.
- FR-003 specifies subsampling to '[deferred] reads per sample', while the Assumptions section later states subsampling to 10,000 reads per sample. The placeholder in the requirement is not explicitly resolved, creating an internal inconsistency.
- FR-005 defines the response variable as the Aitchison distance (Euclidean after CLR transformation), whereas the Idea section’s Methodology Sketch states the response is the Euclidean distance on raw genus‑level abundances. This contradictory definition creates an internal inconsistency.
- The Assumptions section still refers to '[deferred] reads per sample' for subsampling depth, while the Standardized Microbiome Processing principle (VI) and the revised FR‑003 claim a concrete depth of 10,000 reads. The placeholder in Assumptions is unresolved, leading to conflicting specifications.
- FR-005 defines response as Aitchison distance (CLR-transformed), but Idea's Methodology Sketch states 'Euclidean distance on raw genus-level abundances.' These are mathematically different metrics. The spec must be internally consistent on the response variable definition for scientific validity.
- FR-003 has '[deferred] reads per sample' while Assumptions and Edge Cases specify 10,000 reads. This inconsistency must be resolved for internal consistency (noted in kickback concerns).
