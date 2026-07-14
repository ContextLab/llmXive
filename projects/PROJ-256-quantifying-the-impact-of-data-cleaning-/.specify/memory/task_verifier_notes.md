# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — No `tests/integration/test_baseline.py` file or any integration test code is present, and there is no evidence that a `baseline_metrics.json` is generated or that its contents are validated for p‑values in (0, 1) and finite confidence intervals. The required artifact is missing.
- **T012** — The required output file `data/processed/baseline_metrics.json` does not exist, and the provided `code/analysis.py` is incomplete (truncated) with no visible implementation of linear regression, p‑value/CI validation, or JSON writing. The task’s core deliverables are therefore missing.
- **T013** — The required `data/processed/baseline_metrics.json` file is missing, so no baseline metrics have been recorded, let alone with the required precision or for ≥10 datasets. The task’s core deliverable is absent.
- **T023** — The required output file `data/processed/cleaned_metrics.json` is missing, so the task’s deliverable was not produced despite the presence of `code/analysis.py`.
- **T027** — The repository contains only `code/reporting.py`; the required `cleaned_metrics.json` and `baseline_metrics.json` files are absent. Moreover, the `calculate_inconsistency_rate` function is truncated and never returns the computed proportion, so the metrics comparison is not fully implemented.
