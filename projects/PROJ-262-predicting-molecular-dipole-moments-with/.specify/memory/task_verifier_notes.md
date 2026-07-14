# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required file `data/processed/molecules_10k.parquet` is missing, and there is no evidence that `features_3d.parquet` or `features_2d.parquet` were created. The task’s core deliverables are absent.
- **T028** — The provided `train_gnn.py` excerpt defines defaults for seeds, epochs, and early‑stopping patience, but the file is truncated before any training loop, early‑stopping logic, or computation/recording of RMSE variance across the five seeds. Without those sections, the task’s core requirements are not demonstrably satisfied. The next implementer must add (or show) the full script containing the seed loop, early‑stopping implementation, RMSE collection per seed, variance calculation, and recording of that metric.
