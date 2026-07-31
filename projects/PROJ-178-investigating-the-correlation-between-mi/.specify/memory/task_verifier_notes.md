# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — No code, script, or data file implementing the metadata merge logic was provided; there is no artifact (e.g., Python/R script, function, or resulting merged CSV/Parquet) that joins burden, haplogroups, age, sex, population, and PCs as required. The implementer’s claim consists only of a textual description without any concrete implementation or output.
- **T019** — No code, script, configuration, or log file implementing the exclusion of samples with missing age or failed haplogroup assignment was provided; the evidence on disk is empty, so the required exclusion logic cannot be verified.
- **T020** — declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- **T024** — The `code/analysis/model.py` does not rank‑transform PC1 and PC2, never applies the Benjamini‑Hochberg correction, and never writes any output to `code/data/processed/model_results.csv` (the file is missing). Consequently the required regression, adjusted p‑values, and CSV export are not implemented.
- **T027** — The required artifact `code/logs/model_comparison.log` does not exist, so no coefficients or p‑values are recorded as specified. The implementer must create this log file and write the secondary OLS model’s coefficient and p‑value entries into it.
- **T028** — declared artifact(s) missing/empty/invalid: code/data/processed/analysis_results.csv
- **T041** — No `paper/draft.md` file or its contents were provided; without the markdown document showing the required findings and limitations, we cannot confirm that the documentation update was performed. The necessary artifact is missing.
- **T042** — No cleaned or refactored scripts from the `code/analysis/` directory are present; the implementer provided no code artifacts, diff patches, or documentation indicating that the cleanup was performed. Consequently the required output for task T042 is missing.
