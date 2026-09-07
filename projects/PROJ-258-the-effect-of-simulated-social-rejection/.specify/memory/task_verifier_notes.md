# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042** — The repository’s `code/preprocess.py` does not contain a `log_outlier_removal()` implementation (the file ends abruptly and no such function is defined), and the required `data/interim/outlier_log.json` file is absent. Consequently the outlier audit trail cannot be generated as specified.
- **T030** — The generated `reports/final_report.md` does contain the word “associational” but also includes the word “causal”, violating the “excludes causal” requirement, and its sensitivity table uses numeric thresholds (0.01, 0.05, 0.1) instead of the required α levels labeled low, moderate, high. Additionally, the required `data/processed/metadata.json` file is missing, so the function cannot correctly read its dependent data. These issues must be fixed for the task to be considered complete.
