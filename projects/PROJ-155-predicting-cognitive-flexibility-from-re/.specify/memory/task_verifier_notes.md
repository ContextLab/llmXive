# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I looked for the required top‑level folders (`code/`, `data/`, `docs/`, `tests/`) but none are present in the provided artifact list or description. Without these directories the project structure specified in `plan.md` has not been created.
- **T003** — The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8`), nor any evidence that ruff/flake8 and Black were installed or integrated into the project workflow. Consequently, the requirement to configure these tools is not satisfied. The missing artifacts must be added and demonstrated (e.g., runnable lint/format commands passing without errors).
- **T015** — The repository contains `code/utils/motion.py`, but the shown code only defines helper functions and does not include any logic that filters subjects by Mean FD > 0.2 mm or writes entries to `data/processed/exclusion_log.csv`. Moreover, the required `exclusion_log.csv` file is absent from the project. The task’s deliverable (logging excluded subjects with the specified columns) is therefore not present.
- **T015a** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_log.csv, data/results/regression_summary.json
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/final_results.csv
- **T017** — The required `data/processed/exclusion_log.csv` file does not exist, so no row logging the missing behavioral scores was created. The task’s core output is missing, indicating the implementation is incomplete.
