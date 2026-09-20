# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042** — The repository’s `code/preprocess.py` does not contain a `log_outlier_removal()` implementation (the file ends abruptly and no such function is defined), and the required `data/interim/outlier_log.json` file is absent. Consequently the outlier audit trail cannot be generated as specified.
- **T033** — The repository lacks a `save_final_results` implementation in `code/report.py` (the file only defines other helper functions and is truncated before any such function) and the required output file `data/processed/final_results.json` does not exist. Consequently the task of writing the final results with a `p_fdr` column and recording `design_type` is not fulfilled.
