# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or other evidence was provided showing that the required folders (`data/raw`, `data/processed`, `code`, `code/utils`, `code/tests`, `results`, `artifacts`, `specs/001-reward-fidelity-error-recovery/contracts`) actually exist in `projects/PROJ-1052-llmxive-follow-up-extending-long-horizon/`. Without a concrete `ls` output or similar proof, the task requirement is not satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: config.yaml
- **T010** — The required file `code/tests/test_agent_runner.py` does not exist, so the contract test `test_execution_log_schema_validates_task_id_field` is absent. No test code is present to satisfy the task.
- **T011** — The required test file `code/tests/test_baseline.py` is missing entirely, so the integration test `test_baseline_execution_flow_logs_recovery_segments` does not exist. Without this artifact, the task’s requirement cannot be satisfied. The implementer must add the missing test file with the specified test implementation.
- **T013** — The repository contains a partially‑implemented `code/inject_errors.py` (functions are defined but the file is truncated and no code writes the processed trajectories), and the required output `data/processed/injected_trajectories.jsonl` does not exist. The artifact the task demanded is missing, so the requirement is not satisfied.
