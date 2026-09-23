# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence of any `__init__.py` files was provided; the claim lacks the required empty files in the `src/` and `tests/` subdirectories. The implementer must add an empty `__init__.py` to every subdirectory under both `src/` and `tests/`.
- **T042a** — declared artifact(s) missing/empty/invalid: src/analysis/statistical_tests.py, data/batch_config.json
- **T042b** — declared artifact(s) missing/empty/invalid: data/batch_config.json
- **T013** — declared artifact(s) missing/empty/invalid: src/generators/test_generator.py, data/test_instances.json
- **T014** — declared artifact(s) missing/empty/invalid: data/generated_proofs.json, data/generated_grids.json, data/checksums.json
- **T015a** — The repository lacks the required input files (`data/generated_proofs.json`, `data/generated_grids.json`) and the expected output (`data/validation_report.json`). Moreover, the provided `validate_dataset.py` does not demonstrably load a `VALIDITY_THRESHOLD` from `config.py` nor does it show logic for exiting with an error code when thresholds are not met. These missing artifacts and incomplete functionality prevent the task from being satisfied.
- **T015c** — declared artifact(s) missing/empty/invalid: data/generated_proofs.json, data/generated_grids.json, data/test_instances.json, data/validation_report.json
- **T028** — The provided `src/cli.py` does not contain any implementation that runs a single warm‑up run per condition, measures wall‑clock time, estimates total runtime, or aborts when the estimate exceeds 5.5 hours. Moreover, the required `data/batch_config.json` file is absent, so the script cannot even read the seeds needed for the warm‑up. Both the core functionality and a required data artifact are missing.
- **T026** — All required artifacts (`src/analysis/forgetting_metrics.py`, `data/test_instances.json`, `data/results/initial_metrics.json`, `data/results/baseline_metrics.json`, `data/results/final_metrics.json`) are missing, so the evaluation logic and output files were not produced. The task requirements are not satisfied.
