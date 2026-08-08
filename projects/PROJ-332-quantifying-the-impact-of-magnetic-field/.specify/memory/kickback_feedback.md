# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan proposes a one-sided hypothesis test (H1: rho < -0.5) with a Bonferroni correction for only two tests. However, with N=5-10, the power to detect a correlation of r=-0.5 is extremely low (likely < 20%). The plan acknowledges this 'Power Limitation' but proceeds without a formal power analysis or a strategy to mitigate it (e.g., increasing N, relaxing the threshold, or using a Bayesian approach). The study is designed to likely fail to reject the null even if the effect exists.
- The 'Project Structure' section lists `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` as Phase 1 outputs. However, the 'Plan' document itself (Phase 2) references these contracts as if they are already defined. While the structure is logical, the plan should explicitly state that the implementation of these schemas is a prerequisite for the data parsing tasks (US1) to ensure the 'Plan ↔ contracts' consistency is maintained during execution.
