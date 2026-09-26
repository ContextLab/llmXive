# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) or setup scripts are present in the `code/` directory, so the required ruff and black tooling has not been actually configured. The implementer provided no artifacts to verify the task’s completion.
- **T024** — The `data/interim/execution_logs.parquet` file does not exist, so no outcomes are being logged. Moreover, the provided `executor.py` is truncated and lacks concrete logic that detects planner vs. controller failures and appends those labels (and outcomes) to a Parquet log. The required failure‑detection implementation and logging step are therefore missing.
- **T026** — The required artifact `data/interim/execution_logs.parquet` is missing, so no execution metrics have been logged as specified. The task therefore is not satisfied.
