# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The `data/processed/predictions.npy` file is absent, and the provided `train.py` snippet is truncated before it can show saving of predictions or per‑fold Pearson r and R² output. Consequently the script does not demonstrably fulfill the requirement to store outer‑fold predictions or report metrics per fold.
- **T023** — The repository contains `code/modeling/evaluate.py`, but the file is truncated and does not show a complete implementation of the 1,000‑resample bootstrap CI calculation. Moreover, the required data artifact `data/processed/predictions.npy` is absent, so the script cannot be exercised as specified. Both the missing predictions file and the incomplete script prevent the task from being genuinely fulfilled.
