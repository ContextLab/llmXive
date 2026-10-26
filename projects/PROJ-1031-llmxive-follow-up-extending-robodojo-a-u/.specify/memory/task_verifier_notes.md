# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/config.py` file exists and defines `SEED = 42`, but importing it fails because its dependency `code/src/data_loader.py` raises an `ImportError` (the required `datasets` package is not installed). Consequently `cfg.TASK_IDS` is never populated, and the verification command cannot succeed. The missing `datasets` dependency (or a fallback static list) must be provided so that `import code.config` works and yields exactly 18 task IDs.
- **T002** — The three required files (`code/pyproject.toml`, `code/.ruff.toml`, `code/.black.toml`) are present, but there is no evidence that the verification commands (`ruff --config code/.ruff.toml .` and `black --check code/`) were actually executed and returned success. Provide the command output or logs showing zero lint/formatting errors (or a status 0 exit) to satisfy the task.
- **T004** — Requested task execution failed; rerun successfully: code/utils/io.py exit=1
