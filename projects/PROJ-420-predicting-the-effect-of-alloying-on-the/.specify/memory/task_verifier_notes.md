# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/verify_requirements.py exit=1
- **T003** — The repository contains a `code/pyproject.toml` with proper Ruff and Black configuration, but there is no execution evidence (logs, exit codes, or output) showing that `ruff .` and `black .` were run and completed without errors or formatting changes. Without such proof, the task’s verification requirement is not satisfied.
- **T006** — Checked `code/logging_config.py` (exists and defines a RotatingFileHandler with the correct size/backup settings and JSON output matching the schema) and the test log `code/.tasks/T006.tests_test_contracts.py.log` (shows schema‑field test passed). However, there is no evidence that a script was run to emit >10 MiB of logs, no `data/logs/app.log` or its rotated backup files exist, and no sample log entry is shown being validated with `jsonschema.validate`. The required rotation‑behavior verification is missing.
- **T009a** — declared artifact(s) missing/empty/invalid: data/raw/mp_raw.json
- **T009b** — declared artifact(s) missing/empty/invalid: data/raw/nist_alloys.json
- **T009c** — Requested task execution failed; rerun successfully: code/data/merge_sources.py exit=1
