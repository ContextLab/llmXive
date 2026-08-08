# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I looked for the required top‑level folders (`code/`, `data/`, `docs/`, `tests/`) but none are present in the provided artifact list or description. Without these directories the project structure specified in `plan.md` has not been created.
- **T003** — The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8`), nor any evidence that ruff/flake8 and Black were installed or integrated into the project workflow. Consequently, the requirement to configure these tools is not satisfied. The missing artifacts must be added and demonstrated (e.g., runnable lint/format commands passing without errors).
- **T015** — The `code/utils/motion.py` file is truncated and does not contain the logic to filter subjects or write entries to `data/processed/exclusion_log.csv`. Moreover, the required `exclusion_log.csv` file is absent from the repository. Both the implementation and the deliverable log are missing.
- **T015a** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_log.csv, data/results/regression_summary.json
