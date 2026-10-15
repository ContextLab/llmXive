# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan estimates the permutation test will take **≤ 4 h** (see line “estimated ≤ 4 h”), which exceeds the CI runtime limit of **7200 seconds (2 hours)** defined in the specification (FR‑006, SC‑004). This makes the pipeline infeasible under the free‑tier GitHub Actions constraints.
- The data‑model.md does not define the `accuracy_binned.png` and `accuracy_binned.csv` artifacts that the plan references (e.g., in the ‘Stratified Accuracy’ step). Add these files to the data model or remove the references.
- Similarly, `accuracy_vs_hop_raw.png` and `accuracy_vs_hop_raw.csv` are produced by the plan (FR‑005) but are absent from the data‑model.md schema list. Include them in the data model for consistency.
- The `annotated_questions.schema.yaml` contract requires a `predicted_correctness` column, yet the plan’s description of FR‑001 does not mention this column (it only lists `question_id`, `question_text`, `answer_text`, `chain_length`, `status`, `chain_bin`). Clarify that `predicted_correctness` will be produced to satisfy the contract.
