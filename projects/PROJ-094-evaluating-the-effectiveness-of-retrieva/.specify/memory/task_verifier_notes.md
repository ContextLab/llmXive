# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was provided that the listed directories (`src/data`, `src/models`, `src/analysis`, `src/cli`, `src/lib`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`, `tests/contract`) actually exist in the project; the claim is unsubstantiated. The implementer must supply a directory listing or screenshots showing the created structure.
- **T001b** — No `.gitignore` file was presented in the evidence, and thus we cannot confirm that a file containing the required patterns (`__pycache__/`, `*.pyc`, `.env`, `data/raw/`, `data/processed/`, `results/`, `.pytest_cache/`, `*.log`) exists at the repository root. The implementer must add the `.gitignore` with those entries.
- **T002a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T002b** — declared artifact(s) missing/empty/invalid: black.toml
- **T005** — declared artifact(s) missing/empty/invalid: src/data/models.py
- **T013** — declared artifact(s) missing/empty/invalid: src/cli/main.py, results/throughput_report.json
- **T014** — declared artifact(s) missing/empty/invalid: src/cli/main.py
- **T019** — declared artifact(s) missing/empty/invalid: src/data/descriptors.py
- **T020** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, results/correlation_results.json, results/results.csv
- **T020b** — declared artifact(s) missing/empty/invalid: src/analysis/save_baseline_artifacts.py, data/processed/unmasked_baseline_raw.json
