# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002a** — The provided `requirements.txt` exists, but it does not contain pinned (exact) version specifications for the listed packages—most entries lack any version constraint and `pytest`/`pytest-cov` use `>=` instead of `==`. To satisfy the task, each dependency must be pinned to a specific version (e.g., `pytest==7.4.0`, `pandas==2.2.1`, etc.).
- **T002b** — The only artifact provided is the `requirements.txt` file; there is no evidence that a virtual environment was created (e.g., a `venv/` directory, activation script, or `pyvenv.cfg`) nor any logs or records showing that `pip install -r requirements.txt` was executed. Without such proof, the task of creating a virtualenv and installing the listed dependencies is not satisfied.
- **T003** — No configuration files or scripts for ruff or black (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or CI setup) are present in the provided artifact list, so the required linting/formatting setup cannot be confirmed. The implementer must add the appropriate configuration files and any integration steps.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/stats_summary.csv
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/corrected_pvalues.csv
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/summary.csv
- **T029** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.csv
- **T048b** — declared artifact(s) missing/empty/invalid: outputs/performance_report.txt
