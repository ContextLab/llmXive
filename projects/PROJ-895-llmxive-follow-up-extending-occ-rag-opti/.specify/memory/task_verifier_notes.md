# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001.2** — Checked `code/requirements.txt`; it lists each package on a separate line, whereas the task demanded the exact content `torch (cpu-only), transformers, scikit-learn, pandas, numpy, datasets` (a single comma‑separated line). The formatting does not match the specification, so the requirement is not satisfied.
- **T003** — The evidence provided contains no `.flake8` file (or its contents) at the project root, so we cannot confirm that the required configuration with the specified `max-line-length`, `ignore`, and `exclude` settings was created. The task remains unverified.
- **T013** — Requested task execution failed; rerun successfully: code/01_sensitivity_analysis.py exit=1
- **T013.1** — Requested task execution failed; rerun successfully: code/run_original_faithfulness.py exit=1
- **T010.4** — declared artifact(s) missing/empty/invalid: data/processed/critical_subnetwork_ids.csv, data/processed/random_subset_indices.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/edge_case_flags.json
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/pruned_model_weights.pt
- **T022.1** — declared artifact(s) missing/empty/invalid: data/processed/pruned_faithfulness_scores.csv
- **T023.1** — declared artifact(s) missing/empty/invalid: data/processed/paired_scores.csv
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/critical_subnetwork_ids.csv, data/processed/random_subset_indices.csv, data/processed/sensitivity_results.csv
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/statistical_validation_report.json
