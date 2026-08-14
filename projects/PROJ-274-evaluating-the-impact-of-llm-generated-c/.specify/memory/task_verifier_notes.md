# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021c** — The repository lacks the required `data/raw/repo_metrics.json` file, and `code/validation.py` does not use `radon` or `cloc` nor write the collected metrics to that JSON file. The implementation therefore does not meet the task’s specifications.
- **T021b** — The required files `data/raw/repo_selection_rubric.json` and `data/raw/repo_metrics.json` are missing, and the checksum entry in `data/checksums.txt` does not reference the rubric JSON (it references `data/llm_config.yaml`). Therefore the task’s output artifacts are not present or correct.
- **T021e** — declared artifact(s) missing/empty/invalid: data/raw/repo_covariates.json, data/raw/repo_metrics.json, data/raw/repo_matching_report.json
- **T016** — No code, configuration, or JSON output files were provided that implement the required clarification‑question logging, filter by the specified keywords, or expose `help_request_count` and the list of `{timestamp, content}` objects. Consequently the task’s deliverable is missing.
- **T030a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T033** — declared artifact(s) missing/empty/invalid: data/raw/participant_logs.json, data/processed/validation_report.json, schema.yaml
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
