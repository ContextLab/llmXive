# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T027** — The repository contains the preprocessing script, but the required output file `data/processed/alloys_raw.csv` is absent, violating the task’s guarantee that the pipeline must produce this CSV (even for empty data). The missing CSV must be generated and committed.
- **T032** — The provided `feature_engineering_pipeline.py` contains the loading and descriptor‑calculation logic, but the excerpt ends before any code that writes the resulting DataFrame to `data/processed/alloys_features.csv`. Moreover, the required input file `data/processed/alloys_raw.csv` is absent, so the pipeline cannot be exercised to confirm correct behavior. The implementation must include the step that saves the engineered features and be tested with an actual `alloys_raw.csv` file.
