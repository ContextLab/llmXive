# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was presented showing that the directories `code`, `tests`, `data`, and `artifacts` exist under `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`; the claim is unsubstantiated. The required folder structure must be created and verified.
- **T002** — The submission provides no visible evidence that the directories `data/raw`, `data/processed`, and `data/split` actually exist in the repository; no file listings, screenshots, or code creating them are present. Consequently the required data subdirectories are missing.
- **T003** — No evidence was presented showing that the required subdirectories (`artifacts/models`, `artifacts/reports`, `artifacts/figures`) actually exist or contain any files; the claim is unsupported. The next implementer must create these directories (and optionally add placeholder files) and provide a listing or screenshot confirming their presence.
- **T007** — The `code/generate_synthetic.py` script is truncated and never writes the DataFrame to `data/raw/synthetic_baseline.csv` (the line ends with `outpu`). Consequently the required CSV file does not exist. The task’s core requirement—producing a deterministic synthetic dataset saved at the specified path with seed = 42—is not fulfilled.
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T009** — No `.env` file, constants module, or any configuration artifact is present in the provided evidence, and thus there is no evidence that `N_PERMUTATIONS=1000` has been defined for statistical tests. The required environment configuration file is missing.
- **T012** — The required raw file `data/raw/synthetic_baseline.csv` is absent, and the expected output files `data/processed/validated.csv` and `artifacts/reports/validation_log.json` were not generated. Moreover, `code/ingest.py` is truncated and lacks a top‑level orchestration that loads the specified CSV and writes the required outputs. The task’s core requirements are therefore unmet.
- **T018** — The `code/engineer.py` script correctly implements the interaction calculations and checks for the temperature column, but the required output file `data/processed/engineered_features.csv` does not exist, so the primary artifact is missing. The pipeline must be run (or the file added) to produce the engineered features CSV.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/final_dataset.csv
- **T027** — declared artifact(s) missing/empty/invalid: models/kinetic_model.pkl
- **T028** — declared artifact(s) missing/empty/invalid: reports/training_metrics.json
