# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011b** — No synthetic dataset artifact was supplied; there is no file, code, or description showing that a dataset was generated, nor any evidence that it meets the conditional requirements of the task. The implementer’s claim lacks any tangible output.
- **T011d** — No ingestion script, validation logs, or output CSV containing the filtered microbiome‑serology dataset is provided, nor are there any correlation analysis results, CLR‑transformed data, Shannon diversity calculations, or predictive‑modeling artifacts (e.g., Random Forest model files, cross‑validation reports). The required deliverables are missing, so the task is not satisfied.
- **T019a** — No code, notebook, script, or data file was provided that performs or demonstrates conversion of the OTU table to relative abundances, nor any output showing the normalized values. The required artifact for task T019a is missing.
- **T020c** — The `code/02_preprocess.py` script contains a `calculate_shannon_diversity` function, but the required input file `data/processed/data_norm.csv` is absent, so the calculation cannot be performed on real data. Additionally, the script is truncated (`run_shanno` is incomplete), indicating the implementation is not fully functional. The missing data file must be provided (and the script completed) for the task to be satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T032** — No ingestion script, data validation logs, correlation analysis results, or modeling code/output were provided. The required artifacts (e.g., CSV of filtered subjects, Spearman correlation table with raw and BH‑adjusted p‑values, Shannon diversity calculations, and nested‑CV Random Forest performance metrics) are missing, so the task is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: data/results/correlation_results.csv
- **T030d** — declared artifact(s) missing/empty/invalid: data/processed/responder_labels.csv
