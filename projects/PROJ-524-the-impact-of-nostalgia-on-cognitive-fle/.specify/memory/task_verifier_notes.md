# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010a** — The provided `code/ingestion.py` does not implement the required `fetch_data()` function (it imports it from another module) and therefore does not contain the logic to fetch real data, save it to `data/raw/raw_dataset.csv`, or raise `RealDataFetchFailed`. Moreover, the expected raw dataset file `data/raw/raw_dataset.csv` is missing. Both the required artifact and its behavior are absent.
- **T010d** — The repository lacks the required `data/raw/raw_dataset.csv` file, and `code/ingestion.py` does not contain a visible `generate_simulation_data()` function (the shown code only defines `main()` and uses a fetcher). Consequently the core simulation‑data generation logic and its output are missing.
- **T012a** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/processed/cleaned_age_filtered.csv, data/processed/exclusion_counts.json
- **T012b** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_age_filtered.csv, data/processed/cleaned_score_filtered.csv, data/processed/exclusion_counts.json
- **T012d** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/processed/mmse_flag.json
- **T012e** — declared artifact(s) missing/empty/invalid: data/processed/mmse_flag.json, data/processed/cleaned_score_filtered.csv, data/processed/cleaned_dataset.csv, data/processed/cleaned_dataset_no_mmse.csv, data/processed/exclusion_counts.json
- **T012c** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_counts.json, data/processed/exclusion_log.json
- **T014a** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv, data/processed/final_cleaned_dataset.csv
- **T014b** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/processed/validity_metrics.json
- **T017a** — The repository lacks the required `data/processed/final_cleaned_dataset.csv` and the resulting `data/processed/grouped_data.json`. Although `code/analysis.py` contains a `split_by_stimulus_type` function, the file is truncated before any saving logic and no evidence shows the JSON is written. The task’s output artifacts are missing, so the requirement is not satisfied.
- **T018** — The required input file `data/processed/final_cleaned_dataset.csv` is missing, so the analysis cannot actually run on real data. Moreover, the generated `statistical_report.json` does not contain the top‑level keys `p_values` and `t_statistics` as specified (it uses a different structure and even references a different task ID). The implementation therefore does not satisfy the task’s requirements.
- **T044** — The required dataset `data/processed/final_cleaned_dataset.csv` is missing, so the analysis code cannot compute real metrics and cannot be verified to avoid synthetic data generation. The task also expects the code to operate on an existing CSV; without the file the requirement is unmet.
- **T027a** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv, data/processed/cleaned_dataset_no_mmse.csv
- **T027b** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset_no_mmse.csv, data/results/robustness_report.json
