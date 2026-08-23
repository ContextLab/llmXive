# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was presented showing that a `code/` directory actually exists (e.g., a directory listing, screenshot, or output of `os.path.isdir('code')`). Without such proof, we cannot confirm the required artifact is present. The implementer must provide concrete verification that the `code/` folder was created.
- **T001b** — No evidence was provided that a `data/` directory exists in the repository, nor any check (e.g., output of `os.path.isdir('data')`) confirming its presence. The required artifact is missing, so the task is not satisfied.
- **T001c** — No evidence of a `tests/` directory was provided; without an actual folder (and a check like `os.path.isdir('tests')` returning true), the requirement is not satisfied. The implementer must add the `tests/` directory to the project.
- **T001d** — No evidence was provided showing that a `docs/` directory exists (e.g., a directory listing, screenshot, or code confirming `os.path.isdir('docs')` returns True). The required artifact is missing, so the task is not verified as completed.
- **T002** — No `.gitignore` file was provided in the evidence, nor any content showing entries for Python, data, or IDE files. Without the actual artifact, the task requirement is not satisfied.
- **T005** — No evidence of a `data/` folder containing the required `raw`, `processed`, and `interim` subdirectories, nor the accompanying `.gitkeep` files, was provided. The implementer must add these directories and placeholder files to satisfy the task.
- **T012** — declared artifact(s) missing/empty/invalid: code/data/download.py
- **T013** — No code, script, log files, or any other artifact demonstrating error handling for missing reduction levels or corrupted files was provided. Without concrete implementation (e.g., a data‑ingestion pipeline that skips missing entries, logs warnings, and flags low‑reliability samples), the requirement cannot be verified as met. The next implementer must supply the actual script/module and example output/logs showing the described behavior.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_ebsd.parquet
