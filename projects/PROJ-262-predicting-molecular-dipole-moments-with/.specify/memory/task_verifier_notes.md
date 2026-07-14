# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required file `data/processed/molecules_10k.parquet` is missing, and there is no evidence that `features_3d.parquet` or `features_2d.parquet` were created. Without these non‑empty output files, the task’s deliverables are not satisfied.
- **T028** — The provided `train_gnn.py` is cut off mid‑function (`features_3d = [np.array(f) for f i`), contains a syntax error and does not show any training loop, early‑stopping logic, or code that aggregates RMSE across the 5 seeds and writes its variance to `metrics.csv`. Consequently the required functionality is missing.
