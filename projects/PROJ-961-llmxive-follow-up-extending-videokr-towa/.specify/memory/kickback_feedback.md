# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states that “Two‑stage oversampling guarantees ≥ 50 samples per bin” and proceeds without a formal power analysis. A heuristic 50‑sample minimum may be under‑powered to detect modest effect sizes in a permutation change‑point test, especially after Bonferroni correction.
- Only the “disconnection bias” is examined as a confound. Other plausible confounds (e.g., question difficulty, video length, answer type) that could co‑vary with hop count are not modeled, leaving the observed accuracy drop vulnerable to omitted‑variable bias.
- The null model is described as a “Simple linear regression of accuracy on hop count” using per‑bin mean accuracy. This aggregates binary outcomes and applies a linear model, which violates the binomial nature of the data and discards within‑bin variance, reducing statistical power and potentially inflating Type II error.
- The plan states that `annotated_videokr.csv` will contain columns `id, question, answer, chain_length, chain_bin, correctness, status` (see Project Structure and Mapping of Functional Requirements). However, the contract `contracts/annotated_questions.schema.yaml` defines the required fields as `question_id, question_text, answer_text, predicted_correctness, chain_length, status` and does **not** include `chain_bin`. This mismatch means the CSV produced by the pipeline will fail schema validation, violating the contract requirement and breaking downstream verification.
