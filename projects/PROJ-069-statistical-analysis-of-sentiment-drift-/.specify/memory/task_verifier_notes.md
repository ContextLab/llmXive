# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No `.env` file, configuration script, or documentation was presented to demonstrate that FRED API keys and HuggingFace token are managed via environment variables. The required artifact is missing, so the task is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/fred_gdp.csv, data/raw/fred_unrate.csv
- **T017** — declared artifact(s) missing/empty/invalid: data/raw/gdelt_sentiment.csv
- **T018** — The repository lacks the required input file `data/raw/gdelt_sentiment.csv` and the expected output `data/processed/aligned_monthly.csv`. Moreover, the macro‑data resampling uses forward‑fill instead of the specified linear interpolation, and there is no function that merges sentiment and macro series and writes the aligned CSV. These omissions mean the task’s monthly alignment requirement is not fulfilled.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/aligned_monthly.csv, data/processed/data_quality_log.json
