# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The required output file `data/raw/compound_data.json` does not exist, and the provided `code/data/ingestion.py` (as shown) only contains functions for genomic and environmental data with no visible logic for fetching or mocking the compound profiles as specified. Consequently the task’s core requirement is unmet.
- **T015** — The `code/data/preprocessing.py` file shown does not contain any logic for per‑population missingness checks, mean imputation, or logging of exclusion decisions, and the required output file `data/processed/filtered.csv` is absent. Both the core functionality and the expected output artifact are missing.
- **T020** — The provided `preprocessing.py` stops after aggregating data and does not contain any VIF calculation or logging of predictors with VIF > 5. Moreover, the required output file `data/processed/features_vif.csv` is absent. Both the core functionality and the expected artifact are missing.
