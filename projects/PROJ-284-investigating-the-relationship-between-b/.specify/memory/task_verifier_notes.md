# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023a** — The repository contains a partially implemented `run_pca_on_metrics` function, but the script never writes the required CSV files, and the expected output files `data/analysis/pca_loadings.csv` and `data/analysis/factor_scores.csv` are absent. Moreover, the PCA implementation does not guarantee exactly two components or a single factor score column as specified. The task therefore remains unfinished.
- **T023b** — The required output file `data/analysis/full_metrics.csv` does not exist, and the provided `code/analysis/correlations.py` snippet shows no logic for merging raw metrics with PCA factor scores or writing such a CSV. The task’s core requirement is therefore unmet.
