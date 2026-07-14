# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — No `tests/integration/test_baseline.py` file or corresponding integration test is present, and there is no `baseline_metrics.json` output to inspect. Consequently, the required verification of p‑values (0 < p < 1) and finite confidence intervals is not demonstrated. The implementer must add the integration test and provide evidence that it passes with a real `baseline_metrics.json` containing valid metrics.
- **T012** — The repository lacks the required `data/processed/baseline_metrics.json` file, and `code/analysis.py` does not contain a complete implementation using `statsmodels` for linear regression nor any code that validates p‑values/CIs and writes the JSON output. Consequently the baseline analysis and its output are not realized.
