# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `code/requirements.txt` lists the required packages but does not pin them to specific version numbers (e.g., `pandas==1.5.3`), violating the “pinned dependencies” requirement, and it also includes an extra `pyyaml` entry not requested. The task is therefore not fully satisfied.
- **T005** — The provided `code/utils/logger.py` defines a custom `ReproducibilityLogger` but never configures Python’s `logging` module with file and console handlers, nor does it write any output to `logs/pipeline.log`. The task explicitly required setting up logging that writes to that file, which is missing.
- **T006** — The schema file exists and is a valid, strict YAML definition, but there is no accompanying evidence (e.g., Python code or test output) showing that the schema was loaded with `jsonschema`, validated against a good payload, and that it correctly raises an error on a known bad JSON payload as required.
- **T035d** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/processed/volatility_window_3.csv, data/results/regression_window_3.json
- **T035e** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/processed/volatility_window_7.csv, data/results/regression_window_7.json
- **T038** — declared artifact(s) missing/empty/invalid: tests/test_analysis.py
- **T039** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/processed/user_metrics.csv
- **T040** — declared artifact(s) missing/empty/invalid: code/03_analysis.py
- **T041** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/results/diagnostics/vif_report.csv
- **T042** — declared artifact(s) missing/empty/invalid: code/03_analysis.py
- **T043** — declared artifact(s) missing/empty/invalid: code/03_analysis.py
- **T044** — declared artifact(s) missing/empty/invalid: code/03_analysis.py
- **T045** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/results/regression_window_3.json, data/results/regression_window_5.json, data/results/regression_window_7.json, data/results/sensitivity_summary.csv
- **T046** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/results/regression_report.md
- **T047** — declared artifact(s) missing/empty/invalid: code/03_analysis.py, data/results/diagnostics/
- **T048** — declared artifact(s) missing/empty/invalid: code/04_report.py, data/results/regression_report.md, data/processed/user_metrics.csv, data/results/final_report.md
- **T053** — declared artifact(s) missing/empty/invalid: code/run_pipeline.sh
