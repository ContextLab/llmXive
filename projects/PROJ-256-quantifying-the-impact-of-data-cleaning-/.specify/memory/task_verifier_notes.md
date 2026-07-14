# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023** — The `data/processed/cleaned_metrics.json` file exists but contains an empty `"datasets"` list and an error message indicating no cleaned datasets were found, so no t‑test or regression results are recorded. Consequently the required output of metrics for each cleaned variant is missing.
- **T030** — No code, script, or log output implementing the dataset‑size binning (n < 50, 50‑200, > 200) and the required warning behavior is provided. The artifact that should contain the binning logic, dependency on baseline metrics, and the CONSTRAINT_VIOLATION warning is missing, so the task is not satisfied.
- **T033** — No code, script, notebook, or data file implementing the outlier‑threshold sweep, computing false‑positive rates, or calculating inconsistency rates was provided. The required artifact is missing, so the task’s quantitative calculations are not demonstrated.
- **T040** — No comparison report or `ComparisonReport` entity was provided; there is no file, data table, or document containing the required baseline_metrics, cleaned_metrics, absolute and relative differences, or sensitivity analysis. The task’s deliverable is therefore missing.
