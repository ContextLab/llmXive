# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — The required file `src/utils/data_loader.py` does not exist, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so no validation logic was added. The implementer must create/modify the data_loader module and include the schema file to perform the required checks.
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/profiling.py
- **T008a** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T008b** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T009** — declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py
- **T010** — The `tests/contract/test_dataset_schema.py` file is present, but it relies on `contracts/dataset.schema.yaml`, which does not exist in the repository, so the tests cannot actually load or validate against the schema. Without the schema file, the test suite cannot run successfully, meaning the task’s requirement is not genuinely satisfied.
- **T011** — The provided `tests/contract/test_results_schema.py` attempts to load `contracts/results.schema.yaml`, but that schema file is missing from the repository, so the test cannot actually validate any output. Additionally, the displayed contents of the test file are truncated, indicating the implementation may be incomplete. The task’s requirement of having a functional contract test against an existing `results.schema.yaml` is not met.
- **T015a** — The required file `src/gatekeeper/rules.py` does not exist in the repository, so the requested regex‑based rule engine is missing entirely. The implementer must add this file with the specified functionality.
- **T015b** — The required file `src/gatekeeper/rules.py` does not exist, so no code handling malformed deletion log entries or logging to `logs/deletion_errors.log` is present. The task’s core artifact is missing.
- **T012** — The required artifacts `data/processed/access_control_results.json` and `results.schema.yaml` (or `schema.yaml`) are missing from the repository, so no verification can be performed. The task cannot be considered done until both files exist and are validated against each other.
- **T013** — The implementer provided only the task description and specification but no actual artifact—no test script, execution logs, or Access Control score output for the “medical” domain subset. Consequently, there is no evidence that the pipeline was run or that the required score was calculated. The missing concrete test results must be supplied.
- **T014a** — declared artifact(s) missing/empty/invalid: src/gatekeeper/classifiers.py
- **T016** — declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py, schema.yaml
- **T017** — The required source file `src/gatekeeper/pipeline.py` does not exist, and the expected output `data/processed/baseline_results.json` is also missing, so the implementation and result generation cannot be verified.
- **T018** — declared artifact(s) missing/empty/invalid: src/gatekeeper/metrics.py
- **T020** — No code, configuration, or test artifacts showing the added validation‑error logging, exclusion logic, or model‑load retry handling are present. The implementer provided no files or diff that demonstrate the required error‑handling changes, so the task’s requirement cannot be verified as satisfied.
- **T021** — The required file `data/processed/utility_results.json` does not exist, so there is no evidence that it contains the `conditional_utility` and `overall_success` fields. The implementer must create the JSON file with those fields populated.
