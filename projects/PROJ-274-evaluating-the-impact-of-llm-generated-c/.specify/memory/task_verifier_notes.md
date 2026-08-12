# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021c** — The repository lacks the required `data/raw/repo_covariates.json` file, and the provided `code/validation.py` excerpt shows only LOC and cyclomatic complexity calculations without any logic that writes collected metrics to that JSON path. Consequently, the task’s core deliverable—metric collection for covariate adjustment saved to `repo_covariates.json`—is not present.
- **T016** — No code, data file, or JSON output was presented. The required artifact—a JSON file containing the raw help‑request logs (timestamp and content) and the computed composite “Cognitive Load Proxy” score—is missing, so the task’s functional requirements have not been demonstrated.
- **T020** — The required `data/raw/participant_logs.json` file does not exist, and the `update_checksums` function in `code/data_collection.py` is incomplete (truncated) and never called after saving logs, so checksum generation is not actually implemented. The task’s export and checksum requirements are therefore unmet.
- **T033** — The required input file `data/raw/participant_logs.json` does not exist, the schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is missing, and `code/validation.py` contains unrelated metrics code rather than schema‑validation logic that would produce `data/processed/validation_report.json`, which is also absent. The task’s essential artifacts and behavior are not present.
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
- **T036** — declared artifact(s) missing/empty/invalid: data/reports/welch_results.json
- **T037** — declared artifact(s) missing/empty/invalid: data/reports/welch_posthoc.json
- **T037c** — declared artifact(s) missing/empty/invalid: data/reports/ancova_results.json
- **T039** — declared artifact(s) missing/empty/invalid: data/reports/sensitivity_analysis.json
