# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The repository contains a partially shown `code/download_data.py`, but the implementation is truncated and does not clearly write `data/raw/download_status.json` or handle the “invalid” exit case. Moreover, the required `data/raw/download_status.json` file is absent. The task’s output artifact is missing and the script’s behavior cannot be verified as meeting the specification.
- **T013** — The repository lacks the required `data/raw/download_status.json` and the generated `data/raw/synthetic_data.csv`. Moreover, the provided `generate_synthetic_data.py` is truncated and does not show the creation of the `user_response_trigger` column, the correlation check (< 0.05), or the CSV write step, so the implementation does not fully meet the task specifications.
- **T014** — declared artifact(s) missing/empty/invalid: code/preprocess.py
- **T015** — declared artifact(s) missing/empty/invalid: code/preprocess.py, data/processed/raw_processed.csv, data/processed/vif_report.json
- **T016b** — The required artifact `data/processed/modeling_config.json` does not exist, so the code cannot read the `abort_flag` or enforce the N ≥ 80 gate as specified. The missing file must be provided (or generated) for the task to be satisfied.
- **T023** — declared artifact(s) missing/empty/invalid: code/sensitivity_analysis.py, data/results/sensitivity_analysis.csv
- **T026** — declared artifact(s) missing/empty/invalid: data/results/model_metrics.json
