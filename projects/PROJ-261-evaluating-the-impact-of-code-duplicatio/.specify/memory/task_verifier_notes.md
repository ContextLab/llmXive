# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The submitted `code/model_metrics.py` contains a dummy `_dummy_perplexity` that merely counts whitespace‑separated tokens and explicitly avoids loading any model. It does not import bitsandbytes, does not load the `Salesforce/codegen-350M-mono` checkpoint in 8‑bit quantization, and therefore does not compute true model perplexity as required. The core functional requirement is missing.
- **T021** — The repository contains `code/main.py`, but the required output files `data/processed/clone_metrics.csv` (and `perplexity_scores.csv`) are missing, and the script does not actually join or write the metrics to those CSVs. The task’s core requirement—producing the two processed CSV files—is not satisfied.
