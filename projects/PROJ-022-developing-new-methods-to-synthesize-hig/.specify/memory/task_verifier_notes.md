# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure (`code/`, `data/raw`, `data/processed`, `data/reports`, `tests/`, `artifacts/`) was presented or listed in the provided evidence, so the required artifact is missing.
- **T001c** — No `.gitignore` file or its contents were provided; the required ignore patterns (`data/raw/*`, `data/processed/*`, `*.pkl`, `__pycache__`, `*.log`) are absent, so the task is not satisfied.
- **T004** — No directory structure (`data/raw`, `data/processed`) or `.gitignore` files were presented; the claim lacks any tangible artifact showing the required folders and ignore rules. The implementer must provide the actual directories and the `.gitignore` contents that exclude large files.
- **T005** — No `utils/logging_config.py` file or its contents are provided; without the actual module we cannot confirm that structured logging was implemented as required. The evidence needed is the presence of a non‑empty Python file defining the logging configuration.
- **T015** — No code, script, notebook, or data file implementing the “high variance” flagging and exclusion logic was provided. The response contains only the task description and project specifications, without any artifact that could be inspected to verify the required functionality. Consequently, the requirement is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/standardized_polymers.csv
- **T023** — No code, notebook, script, or data file was provided that adds a categorical encoding for the “synthesis method” column to the feature matrix. The required artifact (e.g., a function or pipeline step that transforms the synthesis method into one‑hot or ordinal features and integrates it into the matrix) is missing, so the task is not satisfied.
- **T024** — No `artifacts/model.pkl` file or any evidence of a saved trained model is present; the provided information only describes the feature specifications and user stories, without the required model artifact. The task’s core deliverable is missing.
- **T025** — No artifact (e.g., updated model metadata file, JSON/YAML snippet, or documentation) showing the required explicit disclaimer that findings are associational, not causal was provided. The implementer’s claim cannot be verified without such evidence.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/feature_matrix.csv
