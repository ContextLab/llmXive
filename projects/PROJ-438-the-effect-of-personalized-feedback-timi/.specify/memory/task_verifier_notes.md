# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — The `code/schema.py` file exists, but the required `contracts/dataset.schema.yaml` (or `schema.yaml`) is missing, so the utilities cannot be aligned with the schema as the task demands. The missing schema file must be added for the task to be complete.
- **T018** — No code, script, or log file was provided that shows learners without forum interactions are being filtered out and that the number excluded is being recorded. The required artifact (implementation of the exclusion logic and logging of the exclusion count) is missing.
- **T019** — No code, script, or log file was provided that demonstrates the implementation of the exclusion logic for courses with fewer than 50 learners, nor any evidence that the number of excluded courses is being logged. Without such artifacts, the requirement cannot be confirmed as satisfied.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/learners_raw.csv
- **T021** — The required unit test file `tests/test_intervals.py` does not exist in the repository, so no test code verifying ≥0.1 h precision is provided. The task’s primary artifact is missing.
- **T024** — No code, notebook, script, or data file implementing the median feedback‑interval calculation per learner is present. The required artifact (e.g., a function or pipeline step that computes each learner’s median interval and assigns them to the “Immediate”, “Delayed”, or “Variable” groups) is missing, so the task’s requirement is not satisfied.
- **T025** — No code, script, notebook, or any other artifact implementing the required binning logic (assigning learners to “Immediate”, “Delayed”, or “Variable” groups based on median feedback interval) was provided. Without such a concrete implementation or output, the claim that FR‑004 is satisfied cannot be verified. The missing artifact must be supplied for the task to be considered complete.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/learners_binned.csv
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/results_metrics.csv
- **T036** — declared artifact(s) missing/empty/invalid: data/processed/significance_stability_report.csv
