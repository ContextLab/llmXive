# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `data/`, `results/`, or `tests/` directories (or any files within them) was provided; without a directory listing or actual artifacts, we cannot confirm the project structure was created. The implementer must supply the filesystem layout showing these folders (and ideally some placeholder content) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently the task of configuring these tools is not satisfied.
- **T007** — No files or code were presented showing a `code/models/` directory containing definitions for `Participant`, `MicrobiomeProfile`, or `CognitiveScore`. Without these model files, the required data entities have not been demonstrated as created. The implementer must add the model definitions in the specified path.
- **T009** — No configuration files, scripts, or documentation for managing the UK Biobank token were presented; the implementer provided no tangible artifact showing environment configuration management for credentials. Consequently, the requirement is not satisfied.
- **T019** — The `code/power_analysis.py` script exists, but the required output artifact `results/power/power_report.md` is missing, so the task’s deliverable is not fully satisfied.
- **T012** — declared artifact(s) missing/empty/invalid: code/download.py
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/zero_replaced_counts.parquet
- **T015** — The provided `code/preprocess.py` is truncated and does not contain any genus‑level aggregation, zero‑replacement, CLR or ILR transformation logic, nor does it write `data/processed/ilr_coordinates.parquet`. Moreover, the expected output file is absent. The task’s core requirements are therefore unmet.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cohort_retention_log.json
