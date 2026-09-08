# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — No evidence was provided showing that the four required directories (`code/data/raw/`, `code/data/interim/`, `code/data/processed/`, `code/data/final/`) actually exist; the response contains only the task description and no filesystem artifacts. The implementer must create and list these directories (or provide a directory tree screenshot) to satisfy the requirement.
- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or scripts invoking ruff/black) are present in the `code/` directory, nor any documentation showing they have been set up. The claim lacks any concrete artifact demonstrating that ruff and black are configured.
- **T005a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005d** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006a** — The test file `code/tests/contract/test_symbolic_state.py` exists and uses jsonschema, but the required schema file `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml` is missing, so the test cannot actually perform the validation. The missing schema must be added for the task to be satisfied.
- **T006b** — The test file `code/tests/contract/test_execution_outcome.py` exists and uses `jsonschema`, but the referenced schema `specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml` is missing, so the validation cannot actually be performed. The required schema file must be present for the test to be functional.
- **T006c** — The test file `code/tests/contract/test_compute_metric.py` exists but is truncated (the final test method is incomplete) and it depends on `specs/001-symbolic-dojo-extend/contracts/compute_metric.schema.yaml`, which is missing from the repository. Without the schema file and a complete test suite, the contract validation cannot be performed.
- **T006d** — The test file `code/tests/contract/test_ablation_result.py` exists and uses jsonschema, but the referenced schema file `specs/001-symbolic-dojo-extend/contracts/ablation_result.schema.yaml` is missing, so the validation cannot actually be performed. The required schema artifact must be added for the task to be complete.
- **T000** — declared artifact(s) missing/empty/invalid: data/interim/baseline_results.parquet
- **T007** — declared artifact(s) missing/empty/invalid: code/src/main.py
- **T010** — The provided `controller_adapter.py` only defines the Linear Probe class and some utility functions; it does not implement the required data split, training loop, validation logic, conditional saving of interim and final weights, nor does it raise `ValidationFailedError`. Moreover, the expected weight files `data/processed/adapter_weights_interim.pt` and `data/processed/adapter_weights.pt` are absent.
