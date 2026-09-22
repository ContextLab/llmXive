# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — No evidence was provided showing that the four required directories (`code/data/raw/`, `code/data/interim/`, `code/data/processed/`, `code/data/final/`) actually exist; the response contains only the task description and no filesystem artifacts. The implementer must create and list these directories (or provide a directory tree screenshot) to satisfy the requirement.
- **T005a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005d** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006a** — The test file `code/tests/contract/test_symbolic_state.py` exists and uses jsonschema, but the required schema file `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml` is missing, so the test cannot actually perform the validation. The missing schema must be added for the task to be satisfied.
- **T006b** — The test file `code/tests/contract/test_execution_outcome.py` exists and uses `jsonschema`, but the referenced schema `specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml` is missing, so the validation cannot actually be performed. The required schema file must be present for the test to be functional.
- **T006c** — The test file `code/tests/contract/test_compute_metric.py` exists, but the required schema `specs/001-symbolic-dojo-extend/contracts/compute_metric.schema.yaml` is missing, so the jsonschema validation cannot be performed. Add the missing schema file (and ensure it matches the contract) to satisfy the task.
- **T006d** — The test file `code/tests/contract/test_ablation_result.py` exists and uses jsonschema, but the referenced schema file `specs/001-symbolic-dojo-extend/contracts/ablation_result.schema.yaml` is missing, so the validation cannot actually be performed. The required schema artifact must be added for the task to be complete.
- **T000** — declared artifact(s) missing/empty/invalid: data/interim/baseline_results.parquet
- **T007** — declared artifact(s) missing/empty/invalid: code/src/main.py
- **T010** — The provided `controller_adapter.py` defines a LinearProbe class but does not contain the required data‑splitting, training loop, validation logic, threshold check, or weight‑saving steps, and the expected weight files (`data/processed/adapter_weights_interim.pt` and `data/processed/adapter_weights.pt`) are absent. The task’s core atomic flow is therefore not implemented.
- **T024** — The provided `executor.py` only defines data structures and a mock controller; it contains no logic that detects planner or controller failures nor code that appends any label or outcome to a Parquet file. Moreover, the required `data/interim/execution_logs.parquet` file is absent from the repository. Both the implementation and the output artifact are missing.
- **T026** — The required artifact `data/interim/execution_logs.parquet` is missing, so no execution metrics have been logged as specified. The task therefore is not satisfied.
