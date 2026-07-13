# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required file `data/processed/molecules_10k.parquet` is missing (and there is no evidence that `features_3d.parquet` or `features_2d.parquet` exist), so the task’s output files have not been generated.
- **T028** — The provided `train_gnn.py` file is truncated and does not show a loop over five seeds, a 50‑epoch training regime with early‑stopping (patience = 10), nor any computation and recording of the variance of RMSE across seeds required by SC‑005. The necessary logic is missing or incomplete.
- **T029** — The provided `train_rf.py` defines a `train_one_seed` function but does not contain any code that actually runs it for five different seeds, aggregates the results, or records the RMSE variance as required. Moreover, the file is truncated mid‑function (`write_metrics_csv`) and lacks a main entry point to execute the training pipeline. Consequently, the artifact does not fulfill the task of training a Random Forest baseline with 5 seeds and logging RMSE variance.
