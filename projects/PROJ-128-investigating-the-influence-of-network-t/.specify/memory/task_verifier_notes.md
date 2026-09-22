# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `data/`, `contracts/`, or `tests/` directories is provided; the claim lacks any artifact confirming the directory structure was created.
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015b** — The repository contains `code/preprocess/structural.py`, but it only defines metric calculation and a single‑subject processing function; there is no code that iterates over `DENSITY_THRESHOLD_VARIATIONS` and writes a CSV. Moreover, the required output file `data/processed/structural_density_sensitivity.csv` does not exist. The sensitivity analysis and result export are therefore missing.
- **T017** — The provided `code/preprocess/functional.py` is truncated and never loads `data/processed/loo_centroids_all_subjects.npz` nor implements the per‑subject state‑assignment logic described. Moreover, the required `data/processed/loo_centroids_all_subjects.npz` file is absent. Both the code artifact and the data artifact needed for the task are missing/incomplete.
- **T019** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json
- **T018** — The required output files `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv` are absent, and the referenced `contracts/output.schema.yaml` (schema.yaml) is also missing. Consequently the batch aggregation logic cannot be verified as implemented.
- **T019b** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json, data/processed/structural_metrics.csv, data/processed/completeness_report.json
