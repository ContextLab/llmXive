# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required file `data/processed/molecules_10k.parquet` is missing, and there is no evidence that `features_3d.parquet` or `features_2d.parquet` were created. The task’s core deliverables are absent.
- **T029** — The provided `train_rf.py` file exists and contains code for loading data and training a single Random Forest model, but the excerpt stops before any logic that iterates over the 5 seeds or computes and records the RMSE variance across those runs. Without evidence of a seed loop and variance logging, the task requirement is not demonstrably met.
