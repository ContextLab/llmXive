# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T032** — The required output file `data/processed/null_fpr_metrics.json` does not exist, so the null dataset generation and metric computation have not been provided. Without this artifact, the task’s core requirement is unmet.
- **T033** — No code, script, notebook, or data files implementing the outlier‑threshold sweep, the false‑positive‑rate calculation, or the inconsistency‑rate computation were provided. The claim lacks any concrete artifact to verify that the required calculations (FPR as proportion of p ≤ 0.05 in null datasets and inconsistency rate across thresholds) were actually performed. The next implementer must supply the implementation (e.g., a Python/R script or notebook) and its output demonstrating these metrics per threshold.
