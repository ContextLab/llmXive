# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories `data/results/`, `data/external/`, and `figures/` are missing from the project layout. Consequently the task’s specification to create those folders is not satisfied. (Requirements.txt and quickstart.md are present, but the missing directories cause the overall task to be incomplete.)
- **T002** — The validator imports a relaxed schema at `specs/001-improving-accessibility-and-usability-of/contracts/session_relaxed.schema.yaml`, but this file is missing, causing an import‑time `FileNotFoundError` and preventing the data loader (and its tests) from running. Add the required schema file (or correct the path) so that `validator.validate_session` can load it and the tests can execute.
- **T003** — declared artifact(s) missing/empty/invalid: code/app.py, code/counterbalance.py
- **T004** — The `code/analysis/data_cleaner.py` file exists and implements the required functions, but the pipeline’s output file `data/processed/metrics_summary.csv` is missing, the accompanying `metrics.schema.yaml` is absent, and the integration test `tests/integration/test_cleaning.py` does not exist, so the task’s verification criteria are not met.
