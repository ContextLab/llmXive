# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file list was provided showing that the required folders (`code`, `data/raw`, `data/processed`, `data/interim`, `data/results`, `tests/unit`, `tests/contract`, `tests/integration`, `specs/001-statistical-cognitive-decline/contracts`) actually exist. Without concrete evidence of these paths, the task’s requirement is not satisfied.
- **T003** — The submission contains no visible linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or any documentation showing that ruff/flake8 and Black have been set up. Without these artifacts, the task of configuring the tools is not satisfied.
- **T007** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — No code, configuration, or log files were provided that demonstrate the addition of logging for excluded records with specific reason codes, nor any evidence that the logging parses the cognitive status metadata extraction result. The required artifact (implemented logging logic) is missing.
- **T047** — declared artifact(s) missing/empty/invalid: tests/integration/test_us1_sample.py
- **T024** — The required `data/processed/embeddings.npy` file is absent, and the provided `code/features.py` excerpt does not contain any implementation that computes sentence embeddings with `all-MiniLM-L6-v2` or saves them to that path. Consequently, the semantic feature extraction and storage requirement is not satisfied.
