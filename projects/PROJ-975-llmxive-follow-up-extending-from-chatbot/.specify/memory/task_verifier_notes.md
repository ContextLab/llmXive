# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T004** — Requested task execution failed; rerun successfully: code/generate_data.py exit=1
- **T005** — Checked `code/logging_config.py` (defines the correct `LOG_COLUMNS` and a `get_logger` that should write to `data/results/experiment_log.csv`) and the test suite `tests/contract/test_logging_schema.py`. The required CSV log file `data/results/experiment_log.csv` is missing, and there is no evidence that the tests have been run and passed, so the logging behavior cannot be confirmed. The task needs a created CSV file (or proof that the tests succeed) to satisfy the requirement.
- **T006** — Requested task execution failed; rerun successfully: code/agent.py exit=-1
