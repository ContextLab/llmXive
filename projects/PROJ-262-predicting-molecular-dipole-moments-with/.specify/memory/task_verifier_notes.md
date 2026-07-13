# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required file `data/processed/molecules_10k.parquet` is missing, and there is no evidence that `features_3d.parquet` or `features_2d.parquet` were created. The task’s core deliverables are absent.
- **T028** — The provided `train_gnn.py` file is present but the visible portion only defines a `train_one_seed` function and stops mid‑implementation; there is no evidence of a loop over 5 seeds, early‑stopping logic, computation of RMSE variance across seeds, or recording of that variance to satisfy SC‑005. The required functionality is therefore missing.
- **T029** — The provided `train_rf.py` stops abruptly during the `train_one_seed` function and does not show any loop over five random seeds, nor any code that records or outputs the RMSE variance across those runs. Consequently, the script does not demonstrably fulfill the requirement to train with 5 seeds and log RMSE variance. The missing multi‑seed orchestration and variance‑recording logic must be added.
