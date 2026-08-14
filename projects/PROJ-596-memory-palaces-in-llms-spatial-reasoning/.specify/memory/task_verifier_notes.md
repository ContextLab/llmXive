# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016c** — The repository lacks the required output files `artifacts/results/run_summary.json` and `artifacts/results/runtime_report.json`. Moreover, the shown portion of `code/main.py` does not contain any logic for runtime verification, hyperparameter logging, RAM‑threshold handling, or the generation of the specified JSON reports. Consequently the task’s functional requirements are not met.
- **T027** — The required output file `artifacts/results/interference_metrics.json` does not exist, and the provided `code/main.py` (truncated) shows no implementation that runs interference‑injection experiments, calls T024, or writes the specified fields (`spatial_recall`, `baseline_recall`, `delta`, `p_value`). The task’s core requirements are therefore unmet.
