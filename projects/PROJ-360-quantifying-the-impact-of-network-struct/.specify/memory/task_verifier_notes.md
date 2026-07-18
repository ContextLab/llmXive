# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — declared artifact(s) missing/empty/invalid: data/processed/network_manifest.json
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/metrics.csv
- **T015b** — declared artifact(s) missing/empty/invalid: data/processed/metrics.csv
- **T016** — The repository contains a `code/analyze.py` file, but its content focuses on logging, VIF calculation, and model training rather than computing Pearson and Spearman correlations for the three network metrics, and it does not write a `results/correlations.json` file (the file is missing). Consequently, the required artifact and functionality are not present.
- **T018** — The repository contains `code/analyze.py` but the shown code never checks a sample size `n` or writes warnings to `results/power_analysis.log`. Moreover, the `results/power_analysis.log` file is absent. Both the required logging behavior and the resulting log artifact are missing.
- **T020** — The required input file `data/processed/metrics.csv` does not exist, so the script cannot compute VIF. Moreover, the provided `code/analyze.py` is truncated and shows no code that writes or returns the VIF results, leaving the core functionality unverified. The task’s output (VIF values) is therefore not produced.
- **T021** — The repository lacks the required `results/power_analysis.log` and `data/processed/filtered_features.csv` files, and the shown `code/analyze.py` is truncated before any VIF‑based filtering, logging, or CSV output logic is implemented. Consequently the task’s core requirements are not met.
- **T022** — The required `data/processed/filtered_features.csv` file is absent, and the expected model file `models/thermal_predictor.pkl` was not created. Moreover, the provided `code/analyze.py` is truncated and does not contain the logic to load the filtered features, train a scikit‑learn Linear Regression model, and save it, so the core task is unfulfilled.
