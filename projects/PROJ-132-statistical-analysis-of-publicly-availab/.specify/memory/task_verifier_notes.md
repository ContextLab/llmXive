# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or other evidence was provided to confirm that the required folders (`src/data`, `src/models`, `src/analysis`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`) were actually created; without such proof the task cannot be considered completed.
- **T003a** — No `pyproject.toml` file content was provided, and there is no evidence that a file exists at the repository root containing the required `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (lint.select=['E','F','W','I'], lint.ignore=[]) sections. The implementer must add the file with the exact configuration.
- **T003b** — No `.pre-commit-config.yaml` file or its contents were presented, and the README.md was not shown to contain the required pre‑commit installation instructions. Without these artifacts, the task’s deliverables cannot be verified as completed.
- **T004** — The required file `src/data/download.py` does not exist in the repository (the only referenced `data/download.py` is missing). Hence the task of creating an empty file at the specified path is not satisfied.
- **T005** — The required file `src/data/download.py` (or `data/download.py` as listed) does not exist in the repository, so the implementation cannot be verified. No code or functionality was provided to meet the task’s requirement.
- **T006** — No evidence of a `tests/contract/test_schemas.py` file or a `test_ebird_schema_columns` function is provided; the required test asserting the DataFrame columns and dtypes is missing.
