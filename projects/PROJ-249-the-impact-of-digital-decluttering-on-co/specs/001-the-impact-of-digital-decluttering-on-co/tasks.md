# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and the original research idea. The goal is to implement a reproducible pipeline that validates the associative relationship between digital decluttering and cognitive/affective metrics using a within-subject pre/post design.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the project skeleton and run a "smoke test" pipeline using simulated data to verify that scoring, schema validation, and basic analysis flow from raw inputs to a results file.

- [ ] T001 [P] [US1] Establish project layout, pinned dependencies, and orchestration entry point.
    - Create directory structure: `code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/validation/`, `code/pipeline/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`.
    - Create `code/requirements.txt` (pinned) and `code/config/study_config.yaml` (containing `seed`, `n_participants`, `bootstrap_resamples`, and `practice_effect_grid`).
    - Implement `code/pipeline/run_all.py` to orchestrate the full sequence and `quickstart.md` documenting the execution command.
    - **Verification**: Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` and produce `data/results/pipeline.log` ending with `STATUS: SUCCESS`.

- [ ] T002 [US1] Implement scoring functions for SART, Ospan, PSS-10, and PANAS.
    - Implement logic in `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, and `code/scoring/panas.py` based on OSF v2.1+ reference implementations.
    - Include quality flagging for low attention (e.g., SART accuracy < 50%) as required by FR-009.
    - **Verification**: `pytest code/tests/test_scoring.py` must pass, confirming that raw trial-level inputs are converted to single-value scores conforming to `contracts/dataset.schema.yaml`.

- [ ] T003 [US1] Generate deterministic seeded study simulation and verify raw artifact integrity.
    - Implement `code/validation/simulate_study.py` to produce:
        - `data/raw/participants.csv` (registry).
        - `data/raw/trial_level/` (SART/Ospan raw responses).
        - `data/raw/simulated_measurements.csv` (scored records conforming to `contracts/dataset.schema.yaml`).
        - `data/raw/compliance_logs/` (daily CSVs conforming to `contracts/compliance.schema.yaml`).
    - Implement `code/validation/generate_checksums.py` to create `data/checksums.sha256` for all raw files.
    - Produce a "smoke" output `data/results/smoke_results.json` with one entry per metric conforming to `contracts/analysis.schema.yaml`.
    - **Verification**: `jsonschema.validate` all produced CSVs/JSONs against their respective contracts; `sha256sum -c data/checksums.sha256` must return no errors.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement compliance log processing and plausibility validation.
    - Implement `code/compliance/parse_logs.py` to aggregate daily logs from `data/raw/compliance_logs/`.
    - Enforce FR-010: validate $0 \le \text{minutes} \le 1440$ and flag "0-minute all-7-days" cases.
    - Derive `is_compliant` status ($\le 30$ min social media AND no news AND notifications off).
    - Output `data/processed/aggregated_compliance.csv` and `data/processed/compliance_flags.json`.
    - **Verification**: `pytest code/tests/test_compliance.py` must pass, ensuring correct compliance derivation and loud failure on out-of-range inputs.

- [ ] T005 [US3] Merge datasets, handle attrition, and compute change scores.
    - Implement `code/pipeline/merge_data.py` to join measurements and compliance on `participant_id`.
    - Implement dropout handling: exclude participants missing post-intervention data from paired tests but retain for `data/processed/descriptive_baseline.csv`.
    - Compute $\text{post} - \text{baseline}$ change scores for all metrics and write to `data/processed/change_scores.csv`.
    - **Verification**: `pytest code/tests/test_merge.py` must confirm that change score arithmetic is correct and that participants with missing post-data are excluded from the final analysis set.

- [ ] T006 [US3] Implement primary statistical analysis with bootstrap and Holm-Bonferroni correction.
    - Implement `code/analysis/run_analysis.py` to process `data/processed/change_scores.csv`.
    - For each of the 5 metrics (SART, Ospan, PSS-10, PANAS-PA, PANAS-NA):
        - Compute mean change and 95% CI using 10,000 bootstrap resamples (FR-006).
        - Fallback to Wilcoxon signed-rank test if Shapiro-Wilk $p < 0.05$.
        - Calculate Cohen's $d$ with 95% CI (FR-007).
    - Apply Holm-Bonferroni step-down correction to all p-values (FR-008).
    - Output `data/results/statistical_summary.json` conforming to `contracts/analysis.schema.yaml`.
    - **Verification**: `pytest code/tests/test_analysis.py` must verify that the corrected p-values are strictly $\ge$ uncorrected p-values and that bootstrap CIs contain the empirical mean.

- [ ] T007 [US3] Run Monte-Carlo power simulation for sample size validation.
    - Implement `code/analysis/power_simulation.py` to simulate the pipeline 1,000 times with $d=0.5$.
    - Record the proportion of simulations achieving Holm-Bonferroni corrected significance.
    - Output `data/results/power_analysis.json` containing `power_estimate` and `required_n_for_80pct_power`.
    - **Verification**: Confirm the output JSON contains all required keys and that the result is deterministic given the seed in `study_config.yaml`.

## Phase 3: Reproducible results and paper handoff

- [ ] T008 [US3] Perform sensitivity analysis and document design limitations.
    - Implement `code/analysis/sensitivity.py` to execute:
        1. Analysis excluding participants with compliance $< 50\%$.
        2. Practice-effect simulation: apply the grid `[0.0, 0.2, 0.4]` SD to SART/Ospan and re-calculate effects.
    - Write `data/results/sensitivity_report.md` documenting the self-report limitation (FR-011) and the associational nature of the one-group design (per reviewer feedback).
    - Output `data/results/sensitivity_analysis.json` summarizing the shift in effect sizes.
    - **Verification**: `pytest code/tests/test_sensitivity.py` must confirm the practice-effect grid is applied correctly and the report contains the required limitation sections.

- [ ] T009 [US3] Generate evidence visualizations from validated outputs.
    - Implement `code/viz/generate_plots.py` reading `data/results/statistical_summary.json` and `data/processed/change_scores.csv`.
    - Produce histograms of change scores for all 5 metrics in `figures/`.
    - Produce a forest plot of Cohen's $d$ with 95% CIs in `figures/effect_sizes_forest.png`.
    - **Verification**: `pytest code/tests/test_viz.py` must assert that all PNGs exist and that the plotted mean values match the `statistical_summary.json`.

- [ ] T010 [P] [US3] Compile final associative report and verify full pipeline integrity.
    - Write `data/results/final_report.md` summarizing the methods, the statistical table (mean $\pm$ CI, corrected $p$, $d$), and embedded figures.
    - Frame all findings as **associational** (no causal claims) and evaluate SC-001 through SC-005.
    - Include a "Paper-stage handoff" section mapping JSON keys to planned manuscript tables.
    - Perform a final `sha256sum -c data/checksums.sha256` and log result to `data/results/checksum_verification.log`.
    - **Verification**: `pytest code/tests/test_end_to_end.py` must run the `quickstart.md` command and verify that the final report's statistics match the JSON source of truth.

## Dependencies and requirement coverage

| Requirement | Task(s) | Verification |
|-------------|---------|--------------|
| FR-001 to FR-003 (Scoring/Recruitment) | T002, T003 | `test_scoring.py`, `dataset.schema.yaml` |
| FR-004, FR-010 (Compliance) | T004 | `test_compliance.py`, `compliance.schema.yaml` |
| FR-005 to FR-008 (Analysis/Stats) | T005, T006 | `test_analysis.py`, `analysis.schema.yaml` |
| FR-009 (Quality/Pilot) | T002, T003 | `test_scoring.py` (low-attention check) |
| FR-011 (Sensitivity/Bias) | T008 | `sensitivity_report.md` |
| SC-001 to SC-005 (Success Criteria) | T006, T010 | `statistical_summary.json`, `final_report.md` |
| Reproducibility (Checksums/Logs) | T001, T003, T010 | `checksum_verification.log`, `pipeline.log` |

**Execution Order**: T001 $\rightarrow$ T002 $\rightarrow$ T003 $\rightarrow$ T004 $\rightarrow$ T005 $\rightarrow$ T006 $\rightarrow$ T007 $\rightarrow$ T008 $\rightarrow$ T009 $\rightarrow$ T010.
