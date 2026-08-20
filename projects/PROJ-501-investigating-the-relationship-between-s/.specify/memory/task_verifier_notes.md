# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/` and `tests/` directories is provided; the claim lacks any artifact showing that these folders exist and contain files. The implementer must create and show the directory structure.
- **T002** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/results/`, `data/logs/`, `contracts/`) is present in the provided artifacts; the implementer did not supply any file‑system listing or screenshots showing the structure. The task cannot be considered completed until these directories exist and are non‑empty.
- **T006** — declared artifact(s) missing/empty/invalid: data/processed/merged_filtered.csv, schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The implementer provided no linting or formatting configuration artifacts (e.g., .flake8, .pylintrc, pyproject.toml for black) and the only material shown relates to an unrelated astrophysics data‑processing feature. Consequently, the required linting/formatting setup is missing.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/merged_filtered.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/merged_filtered.csv, data/processed/derived_physics.csv
- **T026** — No code, script, or test files were provided that implement the required validation logic to prevent NaN values in derived columns, nor any evidence (e.g., unit tests, logs, or documentation) showing the logic works for valid inputs. The task therefore lacks the necessary artifact to confirm completion.
- **T030** — declared artifact(s) missing/empty/invalid: data/results/correlation_results.json
- **T032** — declared artifact(s) missing/empty/invalid: data/results/flux_vs_retention.png
- **T033** — No code, script, or documentation was presented that adds console output logic to print a significance statement based on a p‑value < 0.05 and the sign of ρ. The required artifact is missing, so the task is not satisfied.
- **T034** — No artifact (e.g., report, script, or documentation) was provided that shows analysis outputs being explicitly labeled as “associational” only. Without such evidence, the requirement cannot be verified as met.
- **T035** — No README.md content was provided; without seeing the file we cannot confirm that execution instructions and dependency installation steps were added. The required artifact is missing from the evidence.
- **T036** — No ingestion script, output CSV, flux‑calculation module, or integration‑test results were provided; the claim lacks any concrete artifacts to verify that the full pipeline (Ingest → Physics → Analysis → Visualization) was executed and produced the required data and visualizations. The required code, data files, and test outputs are missing.
- **T037** — No timing measurements, benchmark logs, or performance reports are present to demonstrate that the processing completes within 60 seconds on the specified target hardware (SC‑004). Consequently, the required artifact proving the performance requirement is missing.
- **T038** — No pytest output, log, or report is present, and no indication that a test suite was executed or that any tests passed. The required artifact—a proof that the pytest suite ran and met the deferred pass‑rate criteria—is missing.
