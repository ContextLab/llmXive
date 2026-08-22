# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or a `black` config) were provided, so the required setup for `ruff`/`flake8` and `black` cannot be confirmed. The task lacks the necessary artifacts.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The `tests/contract/test_coverage_schema.py` file is present but ends abruptly (`def test_required_co` is cut off), making the test syntactically invalid and non‑functional. Additionally, the required `results/coverage.csv` file does not exist, so the contract test cannot be exercised. The task’s requirement for a complete, runnable contract test is not met.
- **T013a** — The required `data/processed/sampling_report.json` file does not exist, and the provided `code/download.py` excerpt shows only download‑related utilities with no visible stratified‑sampling implementation or code that writes the report. Consequently the task’s deliverable and verification conditions are not satisfied.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/sample_indices_1000.csv
