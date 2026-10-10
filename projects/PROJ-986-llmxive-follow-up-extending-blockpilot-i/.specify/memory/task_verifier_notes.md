# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — declared artifact(s) missing/empty/invalid: specs/001-llmxive-blockpilot-extension/
- **T002** — The `requirements.txt` exists and contains all required packages (plus scipy), but every dependency uses `>=` lower-bound constraints rather than pinned versions (e.g., `transformers>=4.35.0`), which does not satisfy the task's explicit requirement to **pin versions** for reproducibility. The implementer should replace these with exact pins (e.g., `transformers==4.35.0`) or a lockfile-style pinned set.
- **T003** — No artifacts were provided or found on disk for this task — the collector confirms the task references no code/data/figure paths, and there is no evidence of any linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `setup.cfg`, `tox.ini`, or `.flake8`/`black` config) existing in the project. The implementer's claim of configuring ruff/flake8 and black cannot be verified against any actual configuration artifact, so the required tooling setup is missing.
- **T012** — Requested task execution failed; rerun successfully: code/sweep.py exit=1
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/ground_truth.jsonl
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/features.jsonl
- **T027b** — declared artifact(s) missing/empty/invalid: code/train.py
- **T027c** — declared artifact(s) missing/empty/invalid: code/train.py, data/processed/metrics.json
- **T028** — declared artifact(s) missing/empty/invalid: code/train.py
- **T031** — declared artifact(s) missing/empty/invalid: data/processed/training_set.jsonl
- **T031a** — declared artifact(s) missing/empty/invalid: code/uncertainty.py, data/processed/uncertainty_metrics.jsonl
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/feature_importance.json
