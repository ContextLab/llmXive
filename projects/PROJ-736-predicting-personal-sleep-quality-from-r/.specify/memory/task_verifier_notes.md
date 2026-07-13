# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The provided `code/modeling/train.py` is truncated (ends mid‑function, never reaches the part that computes Pearson r, R² per fold, or saves predictions) and the required output file `data/processed/predictions.npy` is absent. Both the script’s full functionality and the saved predictions needed for T023 are missing.
- **T023** — The `evaluate.py` script is present but its implementation is truncated (the `bootstrap_resample_r2` function is incomplete) and the required input file `data/processed/predictions.npy` does not exist, so the bootstrap analysis cannot be performed. The missing prediction data and incomplete code must be provided for the task to be satisfied.
