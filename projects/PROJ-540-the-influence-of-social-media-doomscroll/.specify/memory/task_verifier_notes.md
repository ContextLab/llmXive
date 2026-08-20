# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure evidence (e.g., listings or screenshots of `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`) was provided, so we cannot confirm the required folders exist. The implementer must supply proof that these directories have been created.
- **T001b** — No evidence of the required directory `projects/PROJ-540-the-influence-of-social-media-doomscroll/` or any `__init__.py` files was provided; the claim lacks any artifact showing the source structure exists. The implementer must create the folder and include the `__init__.py` files.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or equivalent) are present in the provided evidence, and the only artifacts shown relate to a different research feature. Consequently the requirement to configure flake8/black is not satisfied.
- **T004b** — `code/config.py` contains the verification and logging functions, but `set_seed` calls `np.random.seed(seed)` without importing `numpy` (np), causing a runtime error and preventing the seed from being applied. Additionally, `code/utils.py` is missing entirely. The task’s requirement of reliably applying and logging the seed is therefore not met.
- **T007** — declared artifact(s) missing/empty/invalid: outputs/analysis.log
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/analysis_data.csv
- **T014** — No code, configuration, or log files were provided that demonstrate logging of row counts, missing‑value statistics, or power‑check results. The claim lacks any tangible artifact showing the required logging functionality was added.
- **T020** — No code, data, or output files were supplied; there is no evidence of a data‑ingestion script, variable extraction, regression model, diagnostics, or visualization required by the user stories. Consequently the required artifacts are missing, so the task is not genuinely completed.
- **T021** — declared artifact(s) missing/empty/invalid: outputs/regression_results.json
- **T022** — declared artifact(s) missing/empty/invalid: outputs/correlation_results.json
- **T027** — declared artifact(s) missing/empty/invalid: outputs/robustness_results.json
- **T029** — declared artifact(s) missing/empty/invalid: outputs/plot.png
- **T030** — declared artifact(s) missing/empty/invalid: outputs/final_report.md
