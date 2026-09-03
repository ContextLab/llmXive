# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file system snapshots were provided showing the required subdirectories (`data/raw`, `data/results`, `code`, `tests/unit`, `tests/contract`, `contracts`). Without concrete evidence that these folders exist and are non‑empty, the task requirement is not satisfied. The implementer must supply a directory tree view or similar proof that the specified subdirectories have been created in the repository.
- **T003** — No `quickstart.md` file was presented; there is no evidence of a non‑empty markdown document containing placeholder text and installation instructions, which is the explicit deliverable of task T003. The required artifact is missing.
- **T004** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T009a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — The `code/logging_config.py` file is truncated (ends with `_handler = `) and never adds the CSV handler or returns a fully configured logger. The provided CSV file’s header omits the `"edge_case"` column defined in `LOG_COLUMNS`, and the required `contracts/experiment_log.schema.yaml` file is missing, so schema compliance cannot be verified.
- **T011** — The provided `tests/contract/test_schemas.py` is incomplete and contains syntax errors (e.g., `for skill i`), and it attempts to load `contracts/task.schema.yaml` which is missing from the repository. Without the schema file and a syntactically correct test, the contract validation cannot be performed.
