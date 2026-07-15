# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `src/`, `tests/`, or `data/` directory (or any files within them) was presented, so the required project structure cannot be confirmed as created. The implementer must supply the actual directory layout and contents.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `pre-commit` setup invoking ruff and black) are present, and the provided artifacts relate to a completely different feature (compression impact) rather than the required linting/formatting setup. The task therefore lacks the necessary configuration artifacts.
- **T006** — No evidence was provided that the `data/raw/`, `data/interim/`, or `data/processed/` directories actually exist in the repository; the response contains only a description of the task without any file‑system listing or screenshots confirming the directory structure. The required artifacts are missing.
- **T007** — No evidence of a `tests/` directory containing the required `unit/`, `integration/`, and `contract/` subfolders is provided; without these artifacts the task requirement is not satisfied.
- **T008** — No pytest configuration file (e.g., pytest.ini, pyproject.toml, or similar) containing coverage thresholds and a 300‑second timeout setting was provided, nor any CI workflow showing these settings. Without such artifacts, the requirement cannot be verified as met.
- **T010** — The provided `tests/unit/test_validate.py` is truncated (ends mid‑function) and thus not a complete, runnable test suite, and the required `src/data/validate.py` module is missing, so the unit test cannot be executed.
- **T012** — declared artifact(s) missing/empty/invalid: src/data/download.py
