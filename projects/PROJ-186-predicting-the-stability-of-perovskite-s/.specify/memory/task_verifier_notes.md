# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No evidence was provided showing that a `data/` directory and a `results/` directory actually exist in the repository, nor that each contains a `.gitkeep` file. The implementer’s claim cannot be verified without these artifacts. The next implementer should add the two directories and place an empty `.gitkeep` file inside each.
- **T008** — No logging configuration file, code snippet, or any other artifact that sets up logging to `logs/pipeline.log` and records exclusion reasons was provided; the claim lacks concrete evidence of the required infrastructure.
- **T013** — The provided `code/data/download.py` only contains Materials Project fetching code and lacks any OQMD CSV download, parsing, or merging logic. Moreover, the suggested alternative file `code/data/download_oqmd.py` does not exist at all, so the task’s requirement to implement explicit OQMD ingestion and conditional merging is not satisfied.
- **T018** — The repository contains `code/data/preprocess.py`, but the script never writes a processed `features.csv` file (it only loads from a non‑existent path and defines split functions). Moreover, the required `data/processed/features.csv` is missing from the project. The task’s core deliverable—saving a cleaned features CSV—is not present.
- **T019** — The required artifact `data/processed/features.csv` does not exist, so there is no way to check for nulls in the `decomposition_energy` column. The implementer must provide the CSV file (non‑empty) and confirm that the specified column contains zero null values.
- **T021** — The required integration test file `tests/integration/test_pipeline.py` is missing, so the specified test cannot be run or verified. No artifact exists to satisfy the task.
- **T026** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T031** — declared artifact(s) missing/empty/invalid: results/model.pkl, results/metrics.json
- **T037** — declared artifact(s) missing/empty/invalid: results/model.pkl
- **T040** — declared artifact(s) missing/empty/invalid: results/screening_full.csv
- **T041** — declared artifact(s) missing/empty/invalid: results/screening_candidates.md
