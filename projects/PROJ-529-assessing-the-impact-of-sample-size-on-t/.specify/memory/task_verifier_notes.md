# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — declared artifact(s) missing/empty/invalid: data/output/success_rate_report.json
- **T016** — The required output file `data/processed/subsample_data.parquet` does not exist, so the logging requirement is not met. Consequently the task’s deliverable is incomplete.
- **T017** — The `code/validate_data.py` file is present but its content is truncated and does not show any logic that computes the success‑rate metrics or writes `data/output/success_rate_report.json`. Moreover, the required JSON report file is missing from the repository. The task’s core output (the summary JSON with the specified fields) is therefore not provided.
- **T023** — The repository contains `code/models.py`, but the required primary output file `data/processed/stability_metrics.csv` does not exist, so the task’s main deliverable is missing. Without this CSV (tagged as “primary”), the implementation does not meet the specification.
- **T024** — The repository lacks the required `data/processed/sensitivity_check.csv` file, and `code/models.py` does not contain a parallel sensitivity‑run implementation that uses REML for all k nor writes results to that CSV. The existing code only fits FE/RE models with a DL/REML rule and writes to a different CSV.
- **T027** — The repository lacks the required `data/processed/sensitivity_analysis_results.csv` file, and the `calculate_sensitivity_analysis` function in `code/metrics.py` is incomplete (no implementation shown for perturbing the estimate, computing variation, or writing results). The task’s core output is therefore missing.
