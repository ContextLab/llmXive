# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T102** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T103** — Requested task execution failed; rerun successfully: code/utils/hash_artifacts.py exit=1
- **T104** — The script `code/03_model/verify_results.py` exists and runs (exit 0) and writes `data/processed/verification_summary.json`, but the required input artifacts `data/models/metrics.json`, `data/processed/feature_ranking.csv`, and `data/processed/class_to_genes.json` are all missing. Consequently the verification cannot perform the AUC‑ROC, mechanism‑blind, and top‑10 ranking checks, and the summary records errors and an overall failure. These files must be provided with valid content for the task to be satisfied.
- **T105** — Requested task execution failed; rerun successfully: code/04_validate/verify_statistics.py exit=1
