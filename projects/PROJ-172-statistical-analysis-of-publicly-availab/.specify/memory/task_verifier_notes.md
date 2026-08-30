# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure is presented in the provided evidence; the required folders (`code/`, `data/raw/`, `data/processed/`, `tests/`, `artifacts/reports/`, `artifacts/figures/`, `state/`) are not shown to exist or contain any files. The implementer must create and verify these directories.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or documentation of their setup are present in the provided evidence, so the requirement to configure ruff/flake8 and Black cannot be confirmed. The task lacks the necessary artifact.
- **T006** — declared artifact(s) missing/empty/invalid: conftest.py
- **T009** — No `.env.example` file was presented, and there is no evidence that a file containing the required variables (`DATA_PATH`, `RANDOM_SEED`, `CI_MODE`) exists in the repository. The implementer must add this file with the specified entries.
- **T012b** — declared artifact(s) missing/empty/invalid: reports/final_report.json
- **T016a** — No code, tests, or documentation implementing the ≥95% data completeness check are present; there is no evidence of a ValueError being raised for real data below the threshold or of flagging “Empirical Hypothesis Untested” in synthetic mode. The required artifact is missing.
- **T016b** — declared artifact(s) missing/empty/invalid: reports/data_completeness_report.json
- **T017** — No logging implementation, configuration, or example output for data ingestion statistics, synthetic fallback triggers, or imputation actions was provided. The claim lacks any code, log files, or documentation demonstrating that the required logging has been added.
