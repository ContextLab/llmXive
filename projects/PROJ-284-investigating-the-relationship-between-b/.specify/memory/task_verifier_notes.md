# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023a** — The repository contains a partially implemented `correlations.py` with functions to compute PCA and save results, but the required output files `data/analysis/pca_loadings.csv` and `data/analysis/factor_scores.csv` are absent (no files exist on disk). Without these non‑empty CSVs containing the specified columns, the task’s deliverables are not satisfied.
- **T023b** — The repository lacks the required `data/analysis/full_metrics.csv` file, and the `correlations.py` script is truncated (the `merge_metri` function is incomplete), so it never writes the combined DataFrame to that path. The task’s core requirement—merging raw metrics with PCA scores and saving them as `full_metrics.csv`—is therefore not fulfilled.
