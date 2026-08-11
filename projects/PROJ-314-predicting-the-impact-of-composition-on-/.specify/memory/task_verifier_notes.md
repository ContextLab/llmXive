# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018c** — The `fetch_materials_project_data()` function in `code/ingestion.py` is truncated and never writes the fetched JSON to `data/raw/materials_project_raw.json`. Moreover, the required output file `data/raw/materials_project_raw.json` does not exist. The task’s core requirements (filtering, error handling, and saving the raw JSON) are therefore not satisfied.
- **T018d** — The repository’s `code/ingestion.py` does not contain a `fetch_nist_data()` implementation (the file is truncated before any such function and only shows other utilities). Additionally, the required output file `data/raw/nist_raw.json` is absent. Both the function implementation and the expected raw data artifact are missing, so the task is not satisfied.
- **T018g** — The repository lacks a `fetch_curated_literature_data()` implementation in `code/ingestion.py` (the file ends before such a function appears) and the required output file `data/raw/curated_literature_raw.json` does not exist. Both the core function and its output artifact are missing, so the task is not satisfied.
- **T017** — The repository lacks the required `data/raw/combined_raw.csv` file, and the provided `code/ingestion.py` does not contain an implementation of `validate_data_gap()` (the function is absent in the shown code). Both the input data and the specified function are missing, so the task is not fulfilled.
- **T054** — declared artifact(s) missing/empty/invalid: data/raw/streamed_final.csv
- **T055** — No evidence of a `logs/sampling_log.txt` file (or any code implementing the fallback sampling with `itertools.islice`) was provided; thus the required artifact is missing, and the task’s logging and sampling requirements have not been demonstrated.
- **T029** — The repository lacks a `run_permutation_test()` implementation in `code/modeling.py` (the provided excerpt shows no such function) and the required output file `data/results/permutation_test_report.json` does not exist. Consequently the permutation‑test logic and reporting artifact are missing.
- **T027d** — declared artifact(s) missing/empty/invalid: data/models/best_model.pkl
- **T041** — declared artifact(s) missing/empty/invalid: data/artifacts/shap_summary.png, data/results/feature_ranking.csv, data/results/stability_metrics.json
- **T056** — declared artifact(s) missing/empty/invalid: data/results/full_pipeline_run.json
