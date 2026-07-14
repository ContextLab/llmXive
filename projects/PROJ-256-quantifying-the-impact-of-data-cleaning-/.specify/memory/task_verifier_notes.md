# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The `code/utils.py` file exists and defines `compute_file_checksum`, but the function is truncated after the existence check and never computes or returns a SHA256 hash. The required checksum logic and return value are missing.
- **T010** — No `tests/integration/test_baseline.py` file or any integration test code was provided, and there is no evidence that a `baseline_metrics.json` is generated and checked for p‑values in (0, 1) and finite confidence intervals. The required test artifact is missing, so the task is not satisfied.
- **T012** — The repository contains a partially‑implemented `code/analysis.py` (truncated, uses SciPy but not statsmodels for linear regression and does not show validation of p‑values or CI finiteness). Crucially, the required output file `data/processed/baseline_metrics.json` is absent, so the baseline metrics are never written. The task’s core deliverables are therefore not satisfied.
- **T013** — The required `data/processed/baseline_metrics.json` file is missing, so no baseline metrics have been recorded, let alone with the required precision or for ≥10 datasets. The task’s core deliverable is absent.
