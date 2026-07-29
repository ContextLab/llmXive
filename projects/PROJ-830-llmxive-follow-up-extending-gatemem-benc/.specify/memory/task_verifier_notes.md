# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — The required file `src/utils/data_loader.py` does not exist, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so no validation logic was added. The implementer must create/modify the data_loader module and include the schema file to perform the required checks.
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/profiling.py
- **T008a** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T008b** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T009** — declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py
- **T010** — The test file `tests/contract/test_dataset_schema.py` exists, but it references a non‑existent schema file (`contracts/dataset.schema.yaml`) and the required `dataset.schema.yaml` is missing entirely. Consequently the test cannot actually validate raw data against the real schema as the task demands. The missing schema file (and incorrect path) must be added/fixed for the task to be complete.
- **T011** — The `tests/contract/test_results_schema.py` file is present, but the referenced schema file `contracts/results.schema.yaml` does not exist, so the test cannot actually validate any output against the required schema. The missing schema file must be added for the task to be fulfilled.
- **T015a** — The required file `src/gatekeeper/rules.py` does not exist in the repository, so the requested regex‑based rule engine is missing entirely. The implementer must add this file with the specified functionality.
- **T015b** — The required file `src/gatekeeper/rules.py` does not exist, so no code handling malformed deletion log entries or logging to `logs/deletion_errors.log` is present. The task’s core artifact is missing.
- **T012** — The required artifacts `data/processed/access_control_results.json` and `results.schema.yaml` (or `schema.yaml`) are missing from the repository, so no verification can be performed. The task cannot be considered done until both files exist and are validated against each other.
- **T014a** — declared artifact(s) missing/empty/invalid: src/gatekeeper/classifiers.py
- **T016** — declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py, schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py, data/processed/baseline_results.json, templates/prompts.yaml
