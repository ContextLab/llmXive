# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — declared artifact(s) missing/empty/invalid: data/raw/elemental_properties.csv
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/completeness_report.json
- **T028b** — The required data file `data/processed/alloys_raw.csv` is missing, so the checker cannot count rows. Moreover, `scarcity_checker.py` does not clearly implement the full workflow (the file is truncated) and writes a JSON flag containing an extra `"message"` field instead of the exact `{"n": N, "threshold": 50}` format. Both the missing input file and the incomplete/incorrect script prevent the task from being satisfied.
- **T032** — The provided `feature_engineering_pipeline.py` is truncated (e.g., an unfinished `process_row` function and no code that writes `alloys_features.csv`). Moreover, the required input file `data/processed/alloys_raw.csv` and the expected output `data/processed/alloys_features.csv` are absent from the repository. Consequently the task’s requirement—to read the raw CSV, compute descriptors, and save the enriched CSV—is not satisfied.
