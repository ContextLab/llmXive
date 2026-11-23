# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The evidence only shows the project root path and contains no linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` / `[tool.ruff]`, `.ruff.toml`, or a `black`/`ruff` config file). Without these artifacts, the task of configuring ruff and black is not satisfied. Adding the appropriate configuration files (and optionally a pre‑commit hook) is required.
- **T035a** — The provided `data/power_config.yaml` is present but does not contain all required keys: it lacks `max_runtime_hours`, `n_runs`, `flat_object_ratio`, and `side_length_bounds`, and thus does not match the specified schema or default values. The missing fields must be added with the concrete numeric defaults for the task to be satisfied.
- **T035b** — The `code/stats/power_analysis.py` correctly reads `data/power_config.yaml` and writes a JSON summary with the required fields, and the output file exists. However, the implementation does not incorporate the “specific subset of ‘flat objects’ required for edge case analysis” into the sample‑size calculation, which the task explicitly demands. Adding logic to handle that subset is needed for completeness.
- **T006c** — declared artifact(s) missing/empty/invalid: code/data/validator.py, results/analysis/pilot_validation.log
- **T006d** — declared artifact(s) missing/empty/invalid: code/data/validator.py, data/raw/synthetic_spatialclaw_v1.json, results/analysis/flat_object_distribution_report.json
- **T008c** — declared artifact(s) missing/empty/invalid: code/data/validator.py, results/analysis/projection_fidelity_report.json
- **T023b** — declared artifact(s) missing/empty/invalid: results/logs/baseline_run.json
- **T017c** — declared artifact(s) missing/empty/invalid: results/runs/, results/analysis/run_count_verification.json
- **T017d** — declared artifact(s) missing/empty/invalid: code/utils/verify_seeds.py, results/logs/execution.log, results/analysis/seed_verification_report.md
- **T053** — declared artifact(s) missing/empty/invalid: code/utils/verify_seeds.py, results/logs/execution.log, results/analysis/seed_verification_report.md
- **T025** — declared artifact(s) missing/empty/invalid: results/analysis/paired_comparison.csv
- **T055** — declared artifact(s) missing/empty/invalid: code/metrics/audit_latency.py, results/logs/execution.log, results/analysis/latency_audit_report.json
- **T054** — declared artifact(s) missing/empty/invalid: code/stats/validate_power.py
- **T061** — declared artifact(s) missing/empty/invalid: code/utils/final_audit.py
- **T052_exec** — Requested task execution failed; rerun successfully: scripts/run_full_pipeline.py exit=1
