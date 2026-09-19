# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence of a logging configuration or error‑handling code was provided in the `code/` directory, nor is there a `logs/` folder or any script that sets up console logging. The required artifact (logging infrastructure) is missing, so the task is not satisfied.
- **T014** — The repository contains `code/preprocessing.py`, but the file is truncated and does not show any code that writes the imputed DataFrame to `data/processed/imputed_data.csv`. Moreover, the missingness‑>50% case logs an error and raises a `ValueError` rather than logging a warning as required. The expected output CSV is absent, so the task is not fully satisfied.
- **T024b** — declared artifact(s) missing/empty/invalid: results/binary_model.csv
- **T026** — declared artifact(s) missing/empty/invalid: results/robustness_metrics.csv
- **T029** — No `model_summary.csv` or `diagnostics.csv` files are present in the provided evidence, and no content for these summary tables is shown. The required CSV artifacts are missing, so the task is not satisfied.
- **T030** — No code, figures, or report files implementing the interaction plot or bootstrap distribution using seaborn/matplotlib were presented. Consequently, the required plotting functions and their embedding in the report are missing.
- **T032** — No PDF report or CSV summary files are provided in the `results/` directory, and there is no evidence of filenames or file‑size checks (≤ 5 MB). The required artifacts are missing, so the task is not satisfied.
- **T033** — No `tests/unit/` directory or test files covering the specified edge cases (missing columns, >50 % missingness, bootstrap timeout) were provided. Without actual unit test code, the requirement to add those tests is not satisfied.
- **T034** — No code, diff, or test artifacts were provided to demonstrate that GPU imports were removed or that loops were refactored for memory efficiency. Consequently, there is no evidence that the repository now complies with the CPU‑only requirement. The implementer must supply the updated source files (or a patch) and a verification script showing the absence of GPU‑related imports and improved memory usage.
