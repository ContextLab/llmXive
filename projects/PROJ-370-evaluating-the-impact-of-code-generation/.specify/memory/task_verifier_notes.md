# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/src/config/settings.py` file is missing, and `code/requirements.txt` does not pin the `detectgpt` package (it appears without a version specifier), violating the task’s specification.
- **T003** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T004** — The `logging_utils.py` and its test pass, but `test_runtime_guard.py` fails (NameError: `json` not imported), so `pytest` does not exit with 0. Additionally, the required schema file `contracts/run_log_event_schema.yaml` is missing, meaning the logger cannot be verified to produce conformant events. Fix the test (import `json`) and provide the schema file to satisfy the task.
