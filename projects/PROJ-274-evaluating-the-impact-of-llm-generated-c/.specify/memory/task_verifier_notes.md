# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021c** — The repository lacks the required `data/raw/repo_metrics.json` file, and `code/validation.py` does not implement metric collection using `radon cc -a -s` and `cloc --json` nor does it write the JSON output. Consequently the task’s output and tool‑specific requirements are not satisfied.
- **T021b** — The required `data/raw/repo_selection_rubric.json` file is missing, and the checksum entry in `data/checksums.txt` refers to `data/llm_config.yaml` instead of the expected JSON file. Consequently, the task’s core outputs and verification steps are not present.
- **T021d** — declared artifact(s) missing/empty/invalid: data/raw/repo_matching_report.json
- **T021f** — The provided `code/validation.py` contains only metric‑analysis utilities and shows no implementation for detecting Setup, API, or Architecture sections, computing a “Human Doc Quality Score”, or writing `data/raw/doc_quality_scores.json`. Moreover, the required JSON output file is absent. The task’s core functionality and output are therefore not delivered.
- **T021e** — declared artifact(s) missing/empty/invalid: data/raw/repo_covariates.json, data/raw/repo_metrics.json, data/raw/repo_matching_report.json, data/raw/doc_quality_scores.json
- **T021h** — The repository contains `code/analysis/ancova_strategy.py`, but the required output file `data/raw/ancova_strategy_config.json` does not exist. Consequently the task’s primary deliverable—producing the ANCOVA strategy configuration JSON—is missing. The implementation must be extended to actually write this file (and ensure it is non‑empty) to satisfy the requirement.
- **T016** — No code, configuration, or JSON output files were provided that implement the required clarification‑question logging, filter by the specified keywords, or expose `help_request_count` and the list of `{timestamp, content}` objects. Consequently the task’s deliverable is missing.
- **T030a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T033** — The validation report exists and indicates success, but the required schema file `contracts/dataset.schema.yaml` is missing, so the validation could not have actually been performed against the specified schema. The task’s prerequisite (ensuring the schema file exists) is not satisfied.
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
- **T036a** — declared artifact(s) missing/empty/invalid: data/reports/primary_analysis_results.json
- **T036b** — declared artifact(s) missing/empty/invalid: data/reports/sensitivity_decision_tree_results.json
- **T037** — declared artifact(s) missing/empty/invalid: data/reports/posthoc_results.json
- **T037c** — declared artifact(s) missing/empty/invalid: data/reports/ancova_results.json
