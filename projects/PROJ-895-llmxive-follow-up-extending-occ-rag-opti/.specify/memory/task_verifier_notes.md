# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001.2** — The `code/requirements.txt` file exists but its contents include comment lines and extra explanatory text, whereas the task demanded the *exact* list of packages (`torch (cpu-only), transformers, scikit-learn, pandas, numpy, datasets`) with no additional lines. The extra comments mean the file does not match the required exact content.
- **T003** — No `.flake8` configuration file was presented or found in the provided evidence, so the required linting setup (max‑line‑length = 88, specified ignores, and exclude list) is missing. The task cannot be considered completed without this file.
- **T013** — Requested task execution failed; rerun successfully: code/01_sensitivity_analysis.py exit=1
- **T013.1** — declared artifact(s) missing/empty/invalid: data/processed/original_faithfulness_scores.csv
- **T010.4** — declared artifact(s) missing/empty/invalid: data/processed/critical_subnetwork_ids.csv, data/processed/random_subset_indices.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/edge_case_flags.json
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/pruned_model_weights.pt
- **T022.1** — declared artifact(s) missing/empty/invalid: data/processed/pruned_faithfulness_scores.csv
- **T023.1** — declared artifact(s) missing/empty/invalid: data/processed/paired_scores.csv
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/critical_subnetwork_ids.csv, data/processed/random_subset_indices.csv, data/processed/sensitivity_results.csv
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/statistical_validation_report.json
