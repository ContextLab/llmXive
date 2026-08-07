# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- **T019** — declared artifact(s) missing/empty/invalid: code/logs/exclusion_report.txt
- **T020** — declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- **T024** — The `calculate_rank_ols` function in `code/analysis/model.py` is truncated and never fits a regression, extracts coefficients/p‑values, or writes results to a CSV. Moreover, the required output file `code/data/processed/rank_ols_results.csv` does not exist. Both the implementation and the expected result artifact are missing.
- **T027** — The required artifact `code/logs/model_comparison.log` does not exist, so no coefficients or p‑values are recorded as specified. The implementer must create this log file and write the secondary OLS model’s coefficient and p‑value entries into it.
- **T032** — declared artifact(s) missing/empty/invalid: code/data/processed/sensitivity_results.csv
- **T033** — The `subgroup_results.csv` file contains only the header (and an extra `n_samples` column) with no actual results, and the provided portion of `sensitivity.py` shows no implementation of a continental‑ancestry subgroup analysis or code that writes the required `ancestry`, `coefficient`, `p_value` rows. The task’s core functionality is therefore missing.
