# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` file exists and is non-empty, but it is **missing a critical required dependency**: `qiime2`. The task explicitly specifies that the project must include `qiime2` in the dependencies, yet the artifact lists only 13 packages (pandas, scikit-learn, statsmodels, biopython, scipy, matplotlib, seaborn, skbio, pytest, ruff, black, isort, pyyaml) without qiime2. The file also includes three additional packages (pytest, ruff, black, isort, pyyaml) not mentioned in the task specification, but the omission of qiime2—which was explicitly required—means the deliverable does not matc
- **T003** — The task requires configuring linting (`ruff`) and formatting (`black`) tools, but the evidence shows critical gaps:

1. **Ruff configuration failed**: The log states "ruff accepted the configuration (exit 1)" — exit code 1 indicates failure, not success. The "OK" label is misleading; a non-zero exit code means ruff rejected the configuration.

2. **Black not installed**: The verification script explicitly notes "black not installed; skipping live check," meaning the formatting tool was never actually configured or validated on the system.

3. **No configuration artifacts shown**: The evidence
- **T006** — The `conftest.py` file exists and contains pytest configuration, but it has critical defects that prevent it from functioning correctly:

1. **Import mismatch with data_models.py**: The `conftest.py` imports `Sample`, `OTU`, and `DiversityMetric` from `code.data_models`, but the actual `data_models.py` defines these classes with different field names. For example:
   - `conftest.py` creates `Sample(ph=7.2, ...)` but `data_models.py` defines the field as `pH` (capital letters)
   - `conftest.py` uses `ph_sd=0.05` but `data_models.py` defines it as `pH_sd`
   - `conftest.py` passes `coordinates=
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/filtered_unified_sample_table.csv
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/unified_sample_table.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/diversity_transformed.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/alpha_diversity_results.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/alpha_diversity_results.csv
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis_log.json
- **T031** — declared artifact(s) missing/empty/invalid: data/processed/beta_balanced_subset.csv, data/processed/beta_diversity_results.csv
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/ordination_coords.csv
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/dbRDA_results.csv
- **T037** — declared artifact(s) missing/empty/invalid: results/summary_report.md
- **T039** — declared artifact(s) missing/empty/invalid: tests/integration/mock_data/, tests/integration/test_runtime_limit.py, state/runtime_log.json
