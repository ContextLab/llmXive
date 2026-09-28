# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`) is presented; the implementer did not provide any file listings or screenshots showing that the structure exists. The task remains unfinished until the full directory hierarchy is created and verified.
- **T001b** — No directory listings or file system evidence were provided showing that the required folders (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`) actually exist; thus the claim cannot be verified. The implementer must create and show the directory structure.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or related setup scripts) are presented in the provided evidence, so the claim that linting (ruff) and formatting (black) have been configured cannot be verified. The required artifacts are missing.
- **T004** — declared artifact(s) missing/empty/invalid: src/lib/utils.py
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- **T006** — declared artifact(s) missing/empty/invalid: src/config.py
- **T007** — declared artifact(s) missing/empty/invalid: src/lib/schema_validator.py
- **T014** — declared artifact(s) missing/empty/invalid: src/metrics/load_stimuli.py
- **T014c** — declared artifact(s) missing/empty/invalid: src/metrics/validate_stimuli.py
- **T011** — declared artifact(s) missing/empty/invalid: src/experiment/pilot_interface.py
- **T012** — The required file `data/measurements/human_ratings.csv` does not exist, so no ratings are persisted and the column requirements cannot be verified. The task is therefore not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/derived/pilot_validation_report.md
- **T022** — No code, data file, correlation result, or flagging mechanism was provided; the claim lacks any tangible artifact (e.g., script rerunning the correlation on the full pilot dataset, a printed Pearson r value, or a generated report/flag). Consequently the requirement to re‑run the correlation and flag r < 0.5 is not demonstrated.
- **T019** — The required output files `data/processed/metrics.csv` and `data/derived/performance_log.txt` are absent, so the pipeline does not produce the mandated artifacts (CSV adhering to the BackgroundFrame schema and a performance log with timing/RAM stats). Without these files, the task’s deliverables are not fulfilled.
- **T020** — No code, test, or documentation was provided showing that the system sets `object_count = 0` for images where the object detector finds no objects. The required artifact (e.g., updated detection pipeline, unit test, or example output) is missing, so the requirement is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/metrics.csv
