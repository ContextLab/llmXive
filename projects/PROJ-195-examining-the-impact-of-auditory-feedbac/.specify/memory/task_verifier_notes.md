# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T025** — declared artifact(s) missing/empty/invalid: data/processed/uncorrected_map.nii.gz, data/processed/fdr_clusters.csv, data/processed/fdr_mask.nii.gz
- **T031** — The repository contains `code/behavior.py`, but the file is truncated and does not include a complete implementation that reads all `data/raw/*/events.tsv` files and writes `data/processed/behavioral_metrics.csv`. Moreover, the required output file `data/processed/behavioral_metrics.csv` is absent. The task’s core deliverable—generating a CSV of mean RTs per subject—is therefore not fulfilled.
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/behavioral_metrics.csv, data/processed/learning_rates.csv
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/roi_betas.csv, data/processed/learning_rates.csv, data/processed/correlation_results.json
- **T034** — The repository contains a `code/viz.py` file, but it only generates a dummy scatter plot with hard‑coded points and does not compute or plot the required regression line or confidence interval. Moreover, the expected output file `figures/brain_behavior_correlation.png` is absent. The visualization script therefore does not fulfill the specification.
