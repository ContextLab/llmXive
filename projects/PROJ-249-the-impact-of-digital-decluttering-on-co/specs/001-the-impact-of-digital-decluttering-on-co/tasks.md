# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and the original research idea. The goal is to implement a reproducible pipeline that evaluates the **associational** (not causal) relationship between one-week digital decluttering and cognitive/affective metrics in a within-subject pre/post design, per the Causal Interpretation Disclaimer in `plan.md`.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the project skeleton and run a verified end-to-end smoke pipeline from seeded simulated study data through scoring, schema validation, and a first real results file. Every task must leave execution evidence (run logs, pytest output), not just files on disk.

- [ ] T001 [P] [US1] Establish project layout, pinned dependencies, and orchestration entry point, with PROOF of a successful end-to-end run.
    - Create directory structure: `code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/validation/`, `code/pipeline/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`.
    - Create `code/requirements.txt` (pinned) and `code/config/study_config.yaml` (containing `seed: 42`, `n_participants`, `bootstrap_resamples: 10000`, and `practice_effect_grid`).
    - Implement `code/pipeline/run_all.py` to orchestrate the full sequence and write `data/results/pipeline.log` ending with `STATUS: SUCCESS`.
    - Document the execution command in `quickstart.md`.
    - **Verification (redo — prior attempt lacked execution evidence)**: Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` and capture the actual run output (exit code 0 and a pytest run of `code/tests/`) into `data/results/pipeline.log`; the log must end with `STATUS: SUCCESS`. A task is not complete until this run log exists and shows a real successful execution.

- [ ] T002 [US1] Implement scoring functions for SART, Ospan, PSS-10, and PANAS.
    - Implement logic in `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, and `code/scoring/panas.py` following the OSF v2.1+ reference scoring algorithms.
    - Include quality flagging for low attention (SART accuracy < 50% → `low_attention` flag) and response-time range checks (100–5000 ms per FR-009).
    - **Verification**: `pytest code/tests/test_scoring.py` must pass, confirming trial-level inputs convert to single-value scores conforming to `contracts/dataset.schema.yaml` (valid ranges: SART commission errors > 0, PSS-10 total 0–40).

- [ ] T003 [US1] Generate deterministic seeded study simulation and verify raw artifact integrity with INSPECTED evidence.
    - Implement `code/validation/simulate_study.py` (seeded, `np.random.seed(42)`) to produce:
        - `data/raw/participants.csv` (registry with pseudonymous IDs matching `^P\d{3}$`, FR-001).
        - `data/raw/trial_level/` (SART/Ospan raw responses).
        - `data/raw/simulated_measurements.csv` (scored records conforming to `contracts/dataset.schema.yaml`).
        - `data/raw/compliance_logs/` (daily CSVs conforming to `contracts/compliance.schema.yaml`).
    - Implement `code/validation/generate_checksums.py` to create `data/checksums.sha256` for all raw files.
    - Produce `data/results/smoke_results.json` with one entry per metric (SART, Ospan, PSS-10, PANAS-PA, PANAS-NA) conforming to `contracts/analysis.schema.yaml`, all values computed from the actual bootstrap output.
    - **Verification (redo — prior attempt lacked inspected evidence)**: a validation script must (a) `jsonschema.validate` every produced file against its contract and print per-file PASS lines, (b) run `sha256sum -c data/checksums.sha256` and print the result, and (c) print the contents of `smoke_results.json` — all captured in `data/results/pipeline.log` so the evidence is inspectable, not assumed.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement compliance log processing and plausibility validation, and EXECUTE it successfully.
    - Implement `code/compliance/compute_compliance.py` (with `parse_logs.py` logic) to aggregate daily logs from `data/raw/compliance_logs/`.
    - Enforce FR-010: validate 0 ≤ minutes ≤ 1440 and flag "0-minute all-7-days" cases as extreme but retained (per spec edge case).
    - Derive `is_compliant` (≤ 30 min social media AND no news AND notifications off); out-of-range inputs must raise loudly — never silently coerced or replaced.
    - Output `data/processed/aggregated_compliance.csv` and `data/processed/compliance_flags.json`.
    - **Verification (redo — prior run exited 1)**: `pytest code/tests/test_compliance.py` must pass AND `python -m code.compliance.compute_compliance` must exit 0 with its output captured in `data/results/pipeline.log`; fix the actual failure before re-checking.

- [ ] T005 [US3] Merge datasets, handle attrition, and compute change scores, and EXECUTE it successfully.
    - Implement `code/pipeline/merge_data.py` to join measurements and compliance on `participant_id` into long format `data/processed/measurement_records.csv`.
    - Handle dropout: exclude participants missing post-intervention data from paired tests but retain them in `data/processed/descriptive_baseline.csv` (per spec edge case); record task administration timestamps.
    - Compute post − baseline change scores for all 5 metrics and write `data/processed/change_scores.csv`.
    - **Verification (redo — prior run exited 1)**: `pytest code/tests/test_merge.py` must confirm change-score arithmetic and dropout exclusion, AND `python -m code.pipeline.merge_data` must exit 0 with output captured in `data/results/pipeline.log`.

- [ ] T006 [US3] Implement primary statistical analysis with bootstrap and Holm-Bonferroni correction.
    - Implement `code/analysis/run_analysis.py` to process `data/processed/change_scores.csv`.
    - For each of the 5 metrics: 10,000-resample bootstrap 95% CI for mean change (FR-006); fallback to Wilcoxon signed-rank only if Shapiro-Wilk p < 0.05 and bootstrap fails; Cohen's d with 95% CI (FR-007).
    - Apply Holm-Bonferroni step-down correction across the outcome family (FR-008).
    - Output `data/results/statistical_summary.json` (single source of truth) conforming to `contracts/analysis.schema.yaml`, with all fields (`metric`, `mean_change`, `ci_lower`, `ci_upper`, `p_value_uncorrected`, `p_value_corrected`, `effect_size_cohen_d`, `n_participants`, `method_used`) computed from real data.
    - **Verification**: `pytest code/tests/test_analysis.py` must verify corrected p-values ≥ uncorrected p-values and that bootstrap CIs contain the empirical mean.

- [ ] T007 [US3] Run Monte-Carlo power simulation for sample size validation.
    - Implement `code/analysis/power_simulation.py` to simulate the analysis pipeline 1,000 times at d = 0.5 with the configured seed.
    - Record the proportion of simulations achieving Holm-Bonferroni-corrected significance.
    - Output `data/results/power_analysis.json` containing `power_estimate` and `required_n_for_80pct_power`.
    - **Verification**: output JSON contains all required keys and is deterministic given the seed; state the power limitation honestly if N is underpowered.

- [ ] T008 [US3] Perform sensitivity analysis and document design limitations, including practice effects.
    - Implement `code/analysis/sensitivity.py` to execute: (1) re-analysis excluding participants with compliance < 50%; (2) practice-effect simulation applying the grid [0.0, 0.2, 0.4] SD to SART/Ospan and recalculating effects — addressing reviewer concern that SART/Ospan improvements may reflect test-retest learning, not the intervention.
    - Write `data/results/sensitivity_report.md` documenting the self-report limitation (FR-011) and the associational (non-causal) framing of the one-group pre/post design.
    - Output `data/results/sensitivity_analysis.json` summarizing the shift in effect sizes across the practice-effect grid.
    - **Verification**: `pytest code/tests/test_sensitivity.py` must confirm the grid is applied correctly and the report contains the required limitation sections.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [US3] Generate evidence visualizations from validated outputs.
    - Implement `code/viz/generate_plots.py` reading `data/results/statistical_summary.json` and `data/processed/change_scores.csv`.
    - Produce histograms of change scores for all 5 metrics and a forest plot of Cohen's d with 95% CIs (`figures/effect_sizes_forest.png`) under `figures/`.
    - **Verification**: `pytest code/tests/test_viz.py` must assert all PNGs exist and plotted values match `statistical_summary.json`.

- [ ] T010 [P] [US3] Compile final associative report and verify full pipeline integrity.
    - Write `data/results/final_report.md` summarizing methods, the statistical table (mean ± CI, corrected p, d), embedded figures, and evaluation of SC-001 through SC-005.
    - Frame all findings as **associational** within-subject changes — no causal claims (Causal Interpretation Disclaimer in `plan.md`); discuss practice effects and self-report bias explicitly.
    - Include a "Paper-stage handoff" section mapping JSON keys to planned manuscript tables; leave PDF compilation and publication to the paper pipeline.
    - Perform final `sha256sum -c data/checksums.sha256` and log to `data/results/checksum_verification.log`.
    - **Verification**: `pytest code/tests/test_end_to_end.py` must re-run the `quickstart.md` command and verify the report's statistics match the JSON source of truth.

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

**Execution order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010. Data-flow constraint: T005 requires T003/T004 outputs; T006 requires T005's `change_scores.csv`; T008–T010 require T006's `statistical_summary.json`.

## Revision notes

- T001, T003, T004, T005 were reopened after independent verification rejected them for missing execution evidence or failed runs; their verification steps now explicitly require captured run logs and exit code 0.
- T008 was strengthened to address reviewer feedback on practice effects in SART/Ospan and the non-causal interpretation of the one-group pre/post design.
