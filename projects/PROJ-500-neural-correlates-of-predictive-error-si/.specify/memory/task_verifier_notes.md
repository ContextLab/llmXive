# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — No repository directory, `.git` folder, or `.gitignore` file is present in the provided evidence; thus the required artifact for initializing a Git repository and configuring its ignore rules is missing.
- **T006** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml`, or a pre‑commit hook invoking ruff/black) are present in the provided artifact list, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No artifact (e.g., configuration files, validation scripts, or documentation) was provided that defines environment variable validation or error‑handling infrastructure. Consequently the requirement to set up such infrastructure is not demonstrated.
- **T016** — The repository lacks the required output files (`data/excluded_subjects.csv` and `data/validation_report.json`). Moreover, `src/data/preprocess.py` is truncated (the `write_excluded_subjects_csv` function is incomplete and no code updates the JSON report), so the artifact‑rejection and underpowered‑subject flagging logic is not fully implemented.
