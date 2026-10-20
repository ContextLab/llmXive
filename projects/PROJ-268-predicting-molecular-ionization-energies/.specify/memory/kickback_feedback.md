# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan schedules 5 stochastic runs for both the baseline and each perturbed configuration (total ≥10 full training runs) plus additional training for the main model, all within a single 6‑hour wall‑clock limit on a free‑tier GitHub Actions runner (2 CPU cores, 7 GB RAM). Empirically, training a 3‑layer GCN on ≥10 k QM9 molecules on CPU typically exceeds several hours per run; combined with ablation and attribution steps this will likely breach the 6 h budget. Split the pipeline into separate jobs or reduce the number of runs to stay within the compute constraints.
