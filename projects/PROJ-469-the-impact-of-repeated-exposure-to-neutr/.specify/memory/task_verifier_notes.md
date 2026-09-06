# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence of a logging configuration or error‑handling code was provided in the `code/` directory, nor is there a `logs/` folder or any script that sets up console logging. The required artifact (logging infrastructure) is missing, so the task is not satisfied.
- **T017a** — The `code/power.py` file is truncated, contains syntax errors (`required_n = fi`) and does not implement writing the required `results/power_design.csv`. Moreover, the `results/power_design.csv` file is absent. The task’s deliverables are therefore not present or functional.
- **T038** — declared artifact(s) missing/empty/invalid: code/data_fetcher.py
- **T014** — The `code/preprocessing.py` file only contains placeholder functions that raise `NotImplementedError`, so MICE imputation, missingness‑rate checking, logging, and CSV output are not implemented. Additionally, the required output file `data/processed/imputed_data.csv` does not exist. The task requirements are therefore not met.
- **T017b** — declared artifact(s) missing/empty/invalid: results/power_analysis.csv
- **T024b** — declared artifact(s) missing/empty/invalid: results/binary_model.csv
- **T022** — The provided `code/robustness.py` snippet ends during the bootstrap function and shows no implementation of an alpha‑sweep routine that evaluates significance at 0.01, 0.05, and 0.10 and writes a CSV. Moreover, the required output file `results/alpha_sweep.csv` is absent from the repository. Both the functional artifact and its result file are missing.
- **T026** — declared artifact(s) missing/empty/invalid: results/robustness_metrics.csv
- **T029** — No `model_summary.csv` or `diagnostics.csv` files are present in the provided evidence, and no content for these summary tables is shown. The required CSV artifacts are missing, so the task is not satisfied.
- **T030** — No code, figures, or report files implementing the interaction plot or bootstrap distribution using seaborn/matplotlib were presented. Consequently, the required plotting functions and their embedding in the report are missing.
