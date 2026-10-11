# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows only a `tests/` directory (with its contents) exists; there is no evidence that the required `src/data_synthesis`, `src/feature_extraction`, `src/baseline`, or `src/scheduler` directories were created in the project root. These missing source folders mean the project structure does not meet the task specification.
- **T003** — The evidence contains no configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or scripts that set up Ruff linting or Black formatting, nor any logs showing these tools were run. Without those artifacts, the task “Configure linting (ruff) and formatting (black) tools” is not satisfied. Adding the appropriate config files and/or documentation of their integration is required.
- **T004** — No pytest configuration file (e.g., pytest.ini or conftest.py) defining CPU‑resource‑limit markers was found in the provided artifact list; without such a file the requirement “Setup `pytest` configuration with CPU resource limit markers” is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/raw/, data/manifest.jsonl
- **T021** — declared artifact(s) missing/empty/invalid: src/feature_extraction/extractor.py
- **T025** — Requested task execution failed; rerun successfully: code/src/feature_extraction/export_features.py exit=1
