# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — Requested task execution failed; rerun successfully: code/src/data/verify_dataset.py exit=1
- **T003** — The `pyproject.toml` file is present and includes proper `ruff` and `black` configuration, but there is no evidence (e.g., command output, logs, or exit‑code records) that `ruff check` and `black --check .` were actually run and exited with code 0. The required verification step is missing.
- **T006** — The file `specs/contracts/game_record.schema.yaml` exists and contains a non‑empty schema, but there is no evidence that its SHA‑256 hash matches the expected CI checksum, nor any test output showing that a pytest schema‑lint passed with a known‑good example. These verification steps are required to consider the task complete.
- **T007** — The artifact `specs/contracts/model_output.schema.yaml` exists, but there is no evidence that its contents exactly match the specification (checksum comparison) nor that the required pytest schema‑lint test (as in T006) was run and passed. Provide the checksum verification and test results to satisfy the task.
