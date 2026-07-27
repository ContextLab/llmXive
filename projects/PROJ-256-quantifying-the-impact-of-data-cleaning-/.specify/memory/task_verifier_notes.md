# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required artifact `data/processed/baseline_metrics.json` does not exist, so no baseline metrics have been recorded (let alone with ≥3‑decimal precision for ≥10 datasets). The task’s core deliverable is missing.
- **T023** — The required output file `data/processed/cleaned_metrics.json` does not exist, so the task’s deliverable is missing. Without this JSON containing the re‑run t‑test and regression metrics, the implementation does not satisfy the stated requirement.
- **T030** — No code, script, or log output implementing the dataset‑size binning sensitivity analysis is provided, nor any evidence that warnings are logged when a bin contains fewer than one dataset. The required artifact (implementation that depends on baseline metrics and logs CONSTRAINT_VIOLATION warnings) is missing.
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/null_fpr_metrics.json
- **T033** — The submission contains only the task description and project specifications; there is no code, script, notebook, or result file that implements the outlier‑threshold sweep, computes false‑positive rates, or calculates inconsistency rates as required. Consequently, the essential artifact demonstrating the required calculations is missing.
- **T040** — No comparison report artifact was supplied; there is no file, data structure, or documented output containing the required fields (baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis). Consequently the task’s deliverable is missing.
