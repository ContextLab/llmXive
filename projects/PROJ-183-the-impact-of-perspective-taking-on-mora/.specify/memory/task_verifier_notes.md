# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — No evidence of the three required directories (`data/raw/`, `data/processed/`, `data/human/`) or the placeholder `.gitkeep` files was provided; without these artifacts the task of initializing the data folders cannot be confirmed as done.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The provided material contains only feature specifications and user stories; there is no `tests/` directory, no `pytest` configuration file (e.g., `pytest.ini`, `conftest.py`), nor any test files. Consequently the required test infrastructure is missing.
- **T016** — declared artifact(s) missing/empty/invalid: code/data/stimuli.py
- **T017** — declared artifact(s) missing/empty/invalid: code/data/stimuli.py
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/stimuli.json
- **T019** — No code, configuration, or log files were supplied that add logging to the data ingestion, filtering, and stratification pipeline. The claim lacks any concrete artifact (e.g., Python module with logging statements, log output examples, or documentation of the logging setup), so the requirement is not met.
- **T051** — The repository lacks any code that computes or logs the mean VADER sentiment difference and writes `data/processed/stratification_report.json`. `code/analysis/stats.py` contains unrelated statistical utilities, and `code/data/stimuli.py` does not exist, nor is the required JSON report present. Implement the validation logic (in either file) and generate the JSON report.
