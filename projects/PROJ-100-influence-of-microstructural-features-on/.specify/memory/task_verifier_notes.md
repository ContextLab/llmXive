# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No `code/` directory or any files within it are present in the provided evidence; the implementer did not supply the required artifact, so the task of creating the `code/` directory is not satisfied.
- **T001b** — No evidence of the required `data/raw/` and `data/processed/` directories is provided; the claim lacks any file system artifact or listing confirming their creation. The task remains undone until those directories exist and are non‑empty.
- **T001c** — No evidence was provided that the `results/` and `results/plots/` directories actually exist on disk; the response contains only a description and no file‑system listing or screenshots confirming their creation. The required artifacts are missing.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the claim that linting (ruff/flake8) and formatting (black) are configured in `code/` cannot be verified. The required artifacts are missing.
- **T010** — declared artifact(s) missing/empty/invalid: tests/unit/test_data_generation.py
- **T011** — The required file `tests/integration/test_data_pipeline.py` does not exist, so no integration test is provided to verify the data cleaning pipeline as specified. The task’s core artifact is missing.
- **T014** — The `code/01_data_acquisition.py` file does not contain the required cleaning/imputation logic (the shown portion ends abruptly and never defines such steps), and the required `results/exclusion_report.log` file is absent. Consequently the task’s specifications are not met.
