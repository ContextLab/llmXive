# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The top‑level `projects/PROJ-496-the-influence-of-simulated-social-valida/` directory exists, but there is no evidence that `.gitkeep` files were created inside `code/`, `tests/`, `docs/`, `data/raw/`, `data/processed/`, and `data/results/` as required by the task. These files are missing or not shown.
- **T002a** — The `requirements.txt` file is present, but it uses “>=” version specifiers instead of exact pinned versions (e.g., `mne==1.5.0`). The task explicitly required pinned versions for all listed packages, which is not satisfied.
- **T003** — The provided `.github/workflows/lint.yml` does not match the required specification: it has a different workflow name, uses branch‑filtered triggers, different action versions, Python 3.10 instead of 3.11, installs extra tools, and runs flake8/black with different arguments (different line length, extra options, different paths). Consequently the task’s exact linting configuration is not fulfilled.
- **T007** — Both required schema files (`eeg_dataset.schema.yaml` and `p300_measure.schema.yaml`) are reported as missing from the `specs/main-feature-sim-social-validation/contracts/` directory, so the task’s deliverables are not present.
- **T004** — The provided `data/` directory contains a top‑level `.gitkeep` but does not include the required `.gitkeep` files inside the `raw`, `processed`, and `results` subfolders, so the exact directory‑structure verification fails.
- **T014** — declared artifact(s) missing/empty/invalid: data/results/categorization_log.json
- **T012b** — declared artifact(s) missing/empty/invalid: data/results/categorization_log.json
- **T015** — declared artifact(s) missing/empty/invalid: data/results/categorization_log.json
- **T057** — declared artifact(s) missing/empty/invalid: code/utils.py
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/epochs_raw.fif
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/p300_measures.csv
- **T026** — declared artifact(s) missing/empty/invalid: data/results/qc_failures.log
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/p300_measures.csv
- **T028a** — declared artifact(s) missing/empty/invalid: data/results/qc_failures.log
- **T051** — Requested task execution failed; rerun successfully: code/analyze.py exit=1
- **T031** — declared artifact(s) missing/empty/invalid: data/results/model_summary.csv
- **T033b** — declared artifact(s) missing/empty/invalid: data/results/model_summary.csv
- **T061** — declared artifact(s) missing/empty/invalid: data/results/threshold_justification.md
- **T044** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_comparison.csv
- **T062** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_comparison.csv
- **T037** — declared artifact(s) missing/empty/invalid: data/results/report.html, data/results/report.pdf
- **T055** — declared artifact(s) missing/empty/invalid: tests/unit/
- **T064** — declared artifact(s) missing/empty/invalid: docs/reproducibility_checklist.md
- **T067** — declared artifact(s) missing/empty/invalid: data/results/sample_size_justification.md
- **T068** — declared artifact(s) missing/empty/invalid: docs/NEGATIVE_FINDING_PROTOCOL.md
