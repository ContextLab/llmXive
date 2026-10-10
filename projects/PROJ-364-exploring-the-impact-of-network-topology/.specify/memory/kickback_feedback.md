# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan does not provide a power analysis or sample‑size justification for detecting the expected correlation between topological metrics and thermal conductivity. With a maximum of 50 samples (≤10 k defects each), the statistical power to detect moderate effect sizes (e.g., r≈0.3) may be insufficient, risking false‑negative conclusions. Add a power calculation (e.g., using expected effect size, α=0.05, desired power = 0.8) and, if needed, adjust the target sample count or analysis strategy accordingly.
- The plan computes a **density‑normalized clustering** metric (`C_norm = C / ρ`) but the `TopologyGraph` entity in `data-model.md` (and the corresponding `graph.schema.yaml`) does not define a field for this metric. This creates a mismatch between the plan and the data model/contract.
- The plan includes a 'population‑level correlation on means when pairwise data missing' (FR‑008). Computing a correlation on aggregated means (e.g., a single mean per metric and a single mean conductivity) is not statistically valid because it yields at most one data point, making correlation undefined. This step should be re‑designed (e.g., use available paired samples only, or employ imputation methods) or removed.
