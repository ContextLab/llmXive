# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006a** — The repository lacks the required `contracts/trajectory.schema.yaml` file, so `parser.py` cannot perform the mandated schema validation. Moreover, the produced `data/processed/metrics_with_moves.csv` contains only the header line and no extracted per‑turn metric rows, indicating that the parser does not actually generate the required output. Both the missing schema and the empty CSV must be addressed for the task to be considered complete.
- **T006b** — The repository contains `code/entropy.py`, but the file only defines helper functions and never reads `data/processed/metrics_with_moves.csv` nor writes `data/processed/entropy_metrics.csv`. The required output file is absent, and the log shows no entropy‑related warnings. Consequently the task’s core functionality and output artifact are missing.
- **T008** — The required output file `data/processed/ablation_labels_train.json` is missing, and the input file `data/raw/agenticsts_trajectories.jsonl` (and the referenced schema) are also absent, so the ablation study could not have been run to generate the ground‑truth labels.
- **T008d** — The log file exists but does not contain a CRITICAL entry as required, and the required `data/processed/fallback_flag.json` file is missing entirely. Consequently the task’s failure‑handling and fallback artifact are not satisfied.
- **T014a** — The provided `code/splitter.py` is truncated, contains syntax errors, and lacks the required edge‑case warning and flag logic. The `edge_case_warnings.log` does not contain the “Statistical power marginal (n < 300)” warning, and the input CSV is empty, resulting in no generated `train_set.csv`, `ablation_train_set.csv`, `validation_set.csv`, or `test_set.csv`. The task’s required outputs and behavior are missing.
- **T014** — The implementer provided only a high‑level feature description and user stories; no code, tests, or other artifacts implementing the required “proxy validation logic” are present. Consequently there is no concrete implementation to verify against the task’s specifications.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/simulation_logs_dynamic.json
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/simulation_logs_static.json, schema.yaml
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/simulation_logs_random.json
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/baseline_comparison.csv, data/processed/build_status.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/token_consistency_report.json
- **T050** — declared artifact(s) missing/empty/invalid: data/processed/divergence_report.json
