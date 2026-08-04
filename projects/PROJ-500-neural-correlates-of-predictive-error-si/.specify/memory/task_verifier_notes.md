# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — No repository directory, `.git` folder, or `.gitignore` file is present in the provided evidence; thus the required artifact for initializing a Git repository and configuring its ignore rules is missing.
- **T006** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml`, or a pre‑commit hook invoking ruff/black) are present in the provided artifact list, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No artifact (e.g., configuration files, validation scripts, or documentation) was provided that defines environment variable validation or error‑handling infrastructure. Consequently the requirement to set up such infrastructure is not demonstrated.
- **T016** — The repository lacks the required output files (`data/excluded_subjects.csv` and `data/validation_report.json`). Moreover, `src/data/preprocess.py` is truncated (the `write_excluded_subjects_csv` function is incomplete and no code updates the JSON report), so the artifact‑rejection and underpowered‑subject flagging logic is not fully implemented.
- **T020** — The repository contains the integration test file, but the required output `data/interim_lagged_mmns.csv` does not exist, so the test cannot verify the correct schema or lagged‑alignment logic. The missing CSV (and any evidence that the test checks its contents) must be generated for the task to be considered complete.
- **T021** — declared artifact(s) missing/empty/invalid: src/data/align.py
- **T022** — declared artifact(s) missing/empty/invalid: src/data/align.py, data/validation_report.json
- **T023** — declared artifact(s) missing/empty/invalid: src/data/align.py
- **T024** — declared artifact(s) missing/empty/invalid: src/data/align.py, data/interim_lagged_mmns.csv
- **T025** — No code, script, or data artifact was provided that shows exclusion of blocks with fewer than 10 valid trials or NaN handling for excessive artifact rejection, nor is there an `aligned_data.csv` output demonstrating the lagged alignment with underpowered subjects excluded. The required implementation and resulting files are missing.
- **T026** — declared artifact(s) missing/empty/invalid: data/interim_lagged_mmns.csv, data/aligned_data.csv
