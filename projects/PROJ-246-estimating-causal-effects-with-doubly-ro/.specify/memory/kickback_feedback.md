# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The `estimation_result.schema.yaml` contract enumerates `outcome_model` values as `nonlinear_correct`, `quadratic`, `interaction_omitted`, but the specification, plan, and tasks (e.g., T005, T006, T007, T008) consistently use the identifier `quadratic_missing_sine`. This mismatch means the pipeline will fail schema validation for any result that uses the intended `quadratic_missing_sine` model, breaking coverage of FR‑001, FR‑002, FR‑004, FR‑006 and SC‑001, SC‑003, SC‑005. Update the contract to include `quadratic_missing_sine` (or rename the model consistently) so that all tasks can satisfy the required schema.
- Task T001 is marked `[P]` (parallel‑safe) but it mutates `spec.md`. Parallel execution with any other task that reads the spec could see a partially‑updated file, violating reproducibility. This task must be run exclusively before any consumer reads the spec, so the `[P]` tag is inappropriate.
- Task T012 validates contracts after all artifacts have been produced. Running it in parallel with any artifact‑writing task (e.g., T007, T010) would cause intermittent validation failures. Therefore `[P]` is unsafe for T012.
- The `outcome_model` enum in `estimation_result.schema.yaml` lists `quadratic`, but the tasks (e.g., T005, T008) produce and reference the value `quadratic_missing_sine`. This mismatch will cause schema validation failures, violating contract constraints.
- Spec's User Story 1 defines the DGP as `Y = sin(X_1) + X_2^2 + ε` (no X₁·X₂ interaction), yet Task T002 implements a DGP with an explicit `0.3·X₁·X₂` interaction term. This diverges from the specification’s acceptance criterion, effectively weakening FR‑001.
- The reproducibility acceptance criterion—"When the random seed is fixed, the generated dataset is identical across repeated runs"—has no corresponding verification step in any task. No test checks that identical seeds produce identical synthetic datasets, so the acceptance criterion is dropped.
