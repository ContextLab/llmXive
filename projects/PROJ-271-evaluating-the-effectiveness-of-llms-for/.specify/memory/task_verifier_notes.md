# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No artifact showing the `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/` directory (e.g., a directory listing, screenshot, or file inside it) was provided, so we cannot confirm that the required directory actually exists. The implementer must supply concrete evidence that the directory was created.
- **T001b** — No directory listings or other evidence were provided showing that `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/data/raw/`, `data/processed/`, or `results/` actually exist. The implementer must supply proof (e.g., a file tree snapshot or `ls` output) that these three directories have been created and are non‑empty.
- **T001c** — No evidence was provided that the required directories `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/tests/unit/` and `tests/contract/` actually exist or contain any files; the claim is unsupported. The implementer must create these directories (and optionally add placeholder test files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) were presented, and the provided project excerpt does not contain any such artifacts. Without concrete, non‑empty config files, the requirement to configure flake8/black is not satisfied.
- **T011** — The repository contains `code/data_pipeline.py`, but the shown content stops before any CSV‑writing logic and does not demonstrate that normalized smell codes are serialized to `data/static_baseline.csv`. Moreover, the required output file `data/static_baseline.csv` is absent from the project. Both the implementation and the generated artifact are missing, so the task is not satisfied.
- **T012** — declared artifact(s) missing/empty/invalid: data/static_baseline.csv
- **T013** — The repository contains `code/semantic_analysis.py`, but the required input file `data/static_baseline.csv` is missing, so the module cannot actually load functions and compute embeddings as specified. Without this CSV the implementation cannot be verified or used.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/semantic_results.json
- **T026** — declared artifact(s) missing/empty/invalid: results/statistical_significance.json
- **T027** — declared artifact(s) missing/empty/invalid: results/logistic_regression.json
- **T028** — declared artifact(s) missing/empty/invalid: results/sensitivity_report.md
