# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or a `black` config) were provided, so the required setup for `ruff`/`flake8` and `black` cannot be confirmed. The task lacks the necessary artifacts.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The provided `tests/contract/test_coverage_schema.py` is truncated (e.g., ends with `def test_nominal_coverage_valu` and lacks the rest of the test suite, causing a syntax error). Additionally, the required `results/coverage.csv` file does not exist, so the contract test cannot be executed. Both artifacts are incomplete or missing.
- **T013a** — The repository lacks the required `data/processed/sampling_report.json` file, and the provided `code/download.py` does not contain any implementation of stratified sampling or generation of the sampling report. Consequently, the task’s deliverable and verification criteria are not satisfied.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/sample_indices_1000.csv
