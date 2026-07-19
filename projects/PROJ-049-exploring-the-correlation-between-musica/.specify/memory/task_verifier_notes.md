# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The `code/ingest.py` file is truncated and does not demonstrate the required timeout download, fallback logging (`FALLBACK: SYNTHETIC`), invocation of `generate_synthetic_data`, mapping, merging, missing‑data handling, or checksum saving. Moreover, the expected output file `data/processed/merged_data.csv` is absent. The task’s core artifacts are therefore missing or incomplete.
- **T017** — The required artifact `data/processed/merged_data.csv` does not exist, so schema verification and checksum logging cannot be performed. The implementer must provide the CSV file (non‑empty with the correct columns) and the corresponding verification/log output.
- **T020** — The repository contains a partially implemented `code/analysis.py` but it never writes the computed Spearman results to `data/processed/correlation_results.csv`, and that CSV file is missing entirely. Consequently the required artifact is absent, so the task is not fulfilled.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/analysis_results.csv
