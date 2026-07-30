# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was presented showing that the directories `code`, `tests`, `data`, and `artifacts` exist under `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`; the claim is unsubstantiated. The required folder structure must be created and verified.
- **T002** — The submission provides no visible evidence that the directories `data/raw`, `data/processed`, and `data/split` actually exist in the repository; no file listings, screenshots, or code creating them are present. Consequently the required data subdirectories are missing.
- **T003** — No evidence was presented showing that the required subdirectories (`artifacts/models`, `artifacts/reports`, `artifacts/figures`) actually exist or contain any files; the claim is unsupported. The next implementer must create these directories (and optionally add placeholder files) and provide a listing or screenshot confirming their presence.
- **T004** — declared artifact(s) missing/empty/invalid: pyproject.toml
- **T007** — The repository contains a partially shown `code/generate_synthetic.py` that sets the seed and defines the model, but the file is truncated and does not include code that writes `data/raw/synthetic_baseline.csv`. Moreover, the expected CSV file is absent from the `data/raw` directory. The required output artifact is missing, so the task is not fulfilled.
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T009** — No `.env` file, constants module, or any configuration artifact is present in the provided evidence, and thus there is no evidence that `N_PERMUTATIONS=1000` has been defined for statistical tests. The required environment configuration file is missing.
- **T012** — The repository lacks the required `data/raw/synthetic_baseline.csv` file, and the expected output files `data/processed/validated.csv` and `artifacts/reports/validation_log.json` are not present. Moreover, `code/ingest.py` is truncated and does not contain logic that actually reads the input and writes the specified outputs. The task’s core artifacts are missing, so the implementation is not complete.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/final_dataset.csv
