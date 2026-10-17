# Tasks: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and canonical schemas in `contracts/`.

This research implements a computational pipeline to aggregate experimental Heusler alloy data, engineer compositional descriptors, and quantify the relationship between composition and magnetic hysteresis (coercivity and saturation magnetization). The study is framed as exploratory due to the known influence of microstructural confounders.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the environment and execute a "thin" slice of the pipeline (Ingest → Preprocess → Feature → Model → Result) on a small real dataset to verify the technical path.

- [ ] T001 Establish the project layout (`code/src/`, `data/raw/`, `data/processed/`, `docs/reports/`), configure pinned dependencies in `code/requirements.txt`, and document the execution command in `quickstart.md`. 
  - **Subtask T001.D**: Create or source the fixed local `data/raw/elemental_properties.csv` containing periodic table data (electronegativity, atomic radii, valence electrons) for all elements in Heusler alloys (Co, Mn, Fe, Ga, Al, etc.) to ensure descriptor consistency per constitution.md:VI; document the source (e.g., "Hand-curated from NIST Chemistry WebBook") and version the file in `data/raw/elemental_properties_v1.csv`. This file is the single source of truth for all descriptor calculations and must not be updated mid-pipeline.

- [ ] T002 Implement a minimal ingestion script in `code/src/ingestion/manual_curator.py` to load `data/raw/manual_curated.csv` (using the template in the spec) and a basic preprocessing script in `code/src/preprocessing/preprocess_pipeline.py` that standardizes units (Oe, emu/g) and filters DFT targets.

- [ ] T003 Implement a baseline descriptor calculator in `code/src/features/descriptor_calculator.py` using the fixed local `data/raw/elemental_properties.csv` and a simple linear regressor in `code/src/models/linear_regressor.py`.

- [ ] T004 Connect these components via `main.py` and run a small valid case (using `data/raw/manual_curated.csv`), producing a result row in `data/results/baseline_metrics.json` containing R² and MAE. **Verification**: This is a Phase 1 sanity check on a small manual dataset; it does NOT depend on T005's full aggregation and runs independently to verify the technical path.

**Checkpoint**: The `main.py` command executes without error and produces a numerical result from real (manual) input.

## Phase 2: Complete the study and validate its evidence

**Goal**: Implement the full scientific pipeline, including robust data aggregation, feature engineering, and statistical validation.

- [ ] T005 Implement the full ingestion suite to aggregate data from ≥3 distinct sources (NIST Materials Data Repository, at least one published journal supplement, and manually curated data from raw literature), saving raw files with checksums to `data/raw/` (FR-001).
  - **Subtask T005.A (Pre-implementation verification)**: Confirm availability of (1) NIST MDR API or downloadable dataset, (2) at least one published journal supplement with Heusler alloy hysteresis data (e.g., a supplementary table from a peer-reviewed paper), and (3) a manual curation target from raw literature (e.g., a list of alloys and properties extracted from papers). Document the three sources in `data/raw/sources_manifest.txt` with URLs/citations and expected data format. **Acceptance criteria**: `sources_manifest.txt` exists and lists the three sources with URLs/citations; attempt to fetch from each source and confirm non-empty response.
  - **Subtask T005.B (Implementation)**: Implement `code/src/ingestion/nist_fetcher.py` and `code/src/ingestion/journal_supplement_parser.py` to ingest from the verified sources (from T005.A) and merge into `data/raw/raw_merged.csv` with checksums recorded in `data/checksums.txt`.
  - **Subtask T005.C (Post-aggregation checkpoint)**: After ingestion, count the total number of unique alloy entries with non-null composition and non-null hysteresis values. Document the count in `data/processed/data_count_verification.json` with fields: `total_entries`, `entries_from_nist`, `entries_from_journal`, `entries_from_manual`, `target_count` (≥50). If `total_entries < 50`, log a warning stating "Data aggregation yielded fewer than 50 entries; statistical power is reduced."

- [ ] T006 Implement the complete preprocessing pipeline in `code/src/preprocessing/preprocess_pipeline.py` to standardize compositions to atomic fractions (summing to 1.0 ± 0.0001), normalize units (coercivity to Oe, saturation magnetization to emu/g), **filter DFT entries using the explicit rule: exclude rows where `source_type == "DFT"` OR `target_source` contains "Materials Project calculated" OR `is_dft == True`**, and apply mean imputation (not MICE) for missing values: if a column has >15% missing rate, perform listwise deletion for that column; otherwise, apply mean imputation with documented imputation rate. Mean imputation is chosen over MICE for exploratory studies on small datasets (N~50) to preserve sample size while maintaining simplicity and reproducibility. Output: `data/processed/alloys_raw.csv` (cleaned data), `data/processed/imputation_log.json` (imputation rates per column), `data/processed/completeness_report.json` (proportion of valid data points per source, satisfying SC-004), and log unique synthesis_method values to `data/processed/synthesis_methods_list.txt` for use in T011. **Verification**: `alloys_raw.csv` contains no DFT entries (check source_type column for absence of "DFT" values and is_dft column for absence of True values), compositions sum to 1.0 ± 0.0001, units are standardized, and `imputation_log.json` shows imputation rates <15% for all imputed columns. `completeness_report.json` contains per-source completeness metrics.

- [ ] T007 Implement the full feature engineering module in `code/src/features/feature_engineering_pipeline.py` to compute ≥5 descriptors for all dataset entries using the fixed local `data/raw/elemental_properties.csv`: (1) average electronegativity (Pauling scale), (2) valence electron concentration (VEC), (3) atomic radii variance, (4) average number of valence d-electrons, and (5) atomic size mismatch. Output: `data/processed/alloys_features.csv` containing all original columns plus the 5 descriptor columns. **Verification**: `alloys_features.csv` has exactly 5 new descriptor columns with no NaN values for any valid entry.

- [ ] T008 Implement the model training pipeline in `code/src/models/training_pipeline.py` to train both a Linear Regression and a Random Forest regressor using 5-fold cross-validation and GridSearchCV for hyperparameter tuning on the fixed [deferred] training split (FR-004). Output: `data/processed/model_metrics.json` containing cross-validation R² and MAE for each model, and trained model artifacts in `code/models/`.
  - **Subtask T008.C (Outlier Detection & Sensitivity)**: Perform outlier detection on the training data using Isolation Forest (contamination=0.1) and document the number of outliers detected. Train models with and without outliers, recording the impact on R² and MAE in `data/results/outlier_analysis.json`. Document whether model performance is robust to outliers or sensitive.

- [ ] T009 Implement the statistical validation suite in `code/src/validation/`:
    - `null_model_comparison.py`: F-test against mean prediction (null model) (SC-001), outputting `f_statistic`, `p_value`, and `is_significant` (p-value < 0.05).
    - `bootstrap_validation.py`: 95% confidence interval for R² using 1000 resamples (SC-002), outputting `r2_lower` and `r2_upper` bounds.
    - `pdp_generator.py`: Partial Dependence Plots for the top 3 features (SC-003), generating `figures/pdp_plots.png`.
    - Output: `data/results/validation_stats.json` and `figures/pdp_plots.png`.
  - **Subtask T009.D (SC-006 Verification)**: Evaluate model performance on the held-out [deferred] test set against the SC-006 threshold (R² ≥ 0.6 AND p-value < 0.05). Document the outcome in `data/results/sc006_evaluation.json` with fields: `r2_test`, `p_value_test`, `threshold_met` (boolean), `interpretation` ("Exploratory Benchmark Met" or "Exploratory Benchmark Not Met — consistent with physical reality given microstructural confounders"). This result will be integrated into `final_report.md` (Section 7) by T011.

- [ ] T010 Implement the microstructure analysis in `code/src/validation/stratified_analysis.py` to group data by `synthesis_method` (if available) and quantify the variance explained by composition versus microstructure. Train models within each synthesis-method stratum and compare results to global models. Output: `data/results/stratified_metrics.json` containing per-stratum R² and MAE, and a note on whether composition effects are consistent across strata. **Integration note**: Stratified results are reported separately in `final_report.md` under Section 6 (Microstructure-Stratified Analysis), supplementing (not replacing) global model results. SC-006 evaluation (Section 7 of final_report.md) uses global model results, not stratified results, to maintain consistency with spec.md SC-006 threshold definition. If synthesis_method is missing for >80% of entries, stratified analysis is skipped and documented as "Insufficient synthesis method metadata for stratification" in `final_report.md`.

**Checkpoint**: All required scientific computations are complete, and artifacts match the actual computations on the full aggregated dataset.

## Phase 3: Reproducible results and paper handoff

**Goal**: Generate the final reporting artifacts, including mandatory scientific disclaimers, and verify the end-to-end reproducibility.

- [ ] T011 Generate the mandatory reporting documents in `docs/reports/`:
    - **`data_scarcity_warning.md`**: Triggered if `total_entries < 50` (check `data/processed/data_count_verification.json`). Content: "**Data Scarcity Warning**: Statistical power is reduced with fewer than 50 data points. The sample size of [N from data_count_verification.json] is below the recommended minimum for robust generalization. Results should be interpreted with caution regarding generalization to unseen alloy compositions. Overfitting risk is elevated."
    - **`statistical_limitations.md`**: ALWAYS generated (regardless of N or p-value). Content: "**Statistical Limitations**: The F-test (p-value from T009 validation_stats.json) validates the statistical fit of the model to the training data, not the physical mechanism underlying magnetic hysteresis. Magnetic hysteresis ($H_c$) is primarily determined by microstructural factors (grain size, defects, domain wall pinning sites) that are not captured by composition alone. Any correlations between composition and hysteresis observed in this study should be interpreted as first-order approximations and may reflect confounded effects of synthesis method or crystal structure, not causal composition-property relationships."
    - **`microstructure_note.md`**: ALWAYS generated (regardless of data availability). Content: "**Microstructural Context**: This dataset includes entries with the following synthesis methods: [Extract unique synthesis_method values from data/processed/synthesis_methods_list.txt (created during T006) and substitute into this template. If synthesis_methods_list.txt is empty or missing, state 'Not specified' instead]. Magnetic hysteresis is heavily influenced by microstructural factors (grain boundaries, defects, domain wall pinning) that depend on synthesis and processing conditions. The composition-hysteresis model in this study should be viewed as a preliminary exploratory analysis that may not generalize to different processing conditions. Future work should incorporate microstructural characterization (e.g., grain size, defect density) as explicit features."
    - **`final_report.md`**: Consolidating all metrics, PDPs, SC-006 evaluation (from T009.D), stratified analysis results (from T010), and outlier analysis (from T008.C). Structure (11 sections in order):
      1. Executive Summary (overview of research question, dataset size, primary findings)
      2. Data Aggregation & Completeness (sources, counts, completeness_report.json metrics)
      3. Feature Engineering (descriptor definitions, descriptor_calculator.py output)
      4. Model Performance — Global (Linear and Random Forest CV metrics from model_metrics.json)
      5. Outlier Analysis (from outlier_analysis.json; robustness assessment)
      6. Microstructure-Stratified Analysis (from stratified_metrics.json; note if skipped due to missing metadata)
      7. SC-006 Evaluation (from sc006_evaluation.json; Exploratory Benchmark result)
      8. Statistical Validation (F-test p-value and result from validation_stats.json, bootstrap CI bounds, interpretation)
      9. Partial Dependence Plots (embed pdp_plots.png and interpret top 3 features)
      10. Statistical Limitations (embed content from statistical_limitations.md)
      11. Microstructural Context & Data Scarcity Notes (embed content from microstructure_note.md and data_scarcity_warning.md if applicable)
      If any upstream task (e.g., T008.C, T010) produces no output due to insufficient data or technical failure, document as "Not applicable — [reason]" rather than causing T011 to fail.

- [ ] T012 Execute the full pipeline from `main.py` in a clean environment, confirm that all output files in `data/processed/`, `data/results/`, and `docs/reports/` are generated and non-empty.
  - **Subtask T012.B (Resource Consumption Verification)**: Monitor and log memory usage and runtime during execution. Output `data/results/resource_consumption.json` with fields: `peak_memory_gb`, `total_runtime_seconds`, `within_limits` (boolean; true if peak_memory < 7 GB AND runtime < 6 hours). Verify that SC-005 (CPU-only execution within GitHub Actions free-tier limits) is satisfied.

- [ ] T013 Calculate SHA256 hashes for all produced artifacts (`data/processed/`, `data/results/`, `docs/reports/`) and update the project state in `state/projects/PROJ-393...yaml` with `artifact_hashes` map and `updated_at` timestamp to ensure a reproducible handoff.

## Dependencies and requirement coverage

| Requirement | Task(s) | Verification |
| :--- | :--- | :--- |
| **FR-001** (3 Sources) | T005.A, T005.B | Check `data/raw/sources_manifest.txt` for three sources; verify `data/raw/raw_merged.csv` contains entries from all three. |
| **FR-002** (Normalization/Imputation) | T006 | Verify `alloys_raw.csv` sums to 1.0 ± 0.0001; check `imputation_log.json` for imputation rates <15%; confirm no DFT entries in `source_type` column; verify mean imputation is applied (not MICE). |
| **FR-003** (5 Descriptors) | T007 | Verify `alloys_features.csv` has exactly 5 new descriptor columns with no NaN values. |
| **FR-004** (LR/RF + CV) | T008 | Check `model_metrics.json` for both model types and cross-validation scores. |
| **FR-005** (F-test/Bootstrap/PDP) | T009 | Verify `validation_stats.json` and `figures/pdp_plots.png` exist and contain expected results. |
| **FR-008** (DFT Filter/Scarcity) | T006, T011 | Check for absence of DFT entries in `alloys_raw.csv` using explicit rule (source_type, target_source, is_dft columns); verify `data_scarcity_warning.md` is generated if N<50. |
| **FR-009** (Fit vs Mechanism) | T011 | Verify `statistical_limitations.md` contains the mandatory disclaimer about F-test validity and microstructural confounders, anchored to T009 F-test output. |
| **FR-010** (Microstructure) | T006, T010, T011 | Verify `synthesis_methods_list.txt` is created during T006; verify `stratified_metrics.json` exists; verify `microstructure_note.md` documents synthesis methods extracted from synthesis_methods_list.txt. |
| **SC-001** (F-test) | T009 | Check `validation_stats.json` for `f_statistic` and `p_value`. |
| **SC-002** (Bootstrap CI) | T009 | Check `validation_stats.json` for `r2_lower` and `r2_upper` (95% CI from 1000 resamples). |
| **SC-003** (PDPs) | T009 | Verify `figures/pdp_plots.png` exists and shows top 3 features. |
| **SC-004** (Completeness) | T005.C, T006 | Verify `data_count_verification.json` and `completeness_report.json` report proportion of valid data points per source. |
| **SC-005** (CPU/RAM Limits) | T012.B | Verify `resource_consumption.json` shows peak_memory < 7 GB and runtime < 6 hours. |
| **SC-006** (Exploratory Benchmark) | T009.D | Check `sc006_evaluation.json` for R² and p-value against threshold; verify result is documented in `final_report.md` Section 7. |
| **Constitution VI** (Descriptor Consistency) | T001.D, T007 | Verify `data/raw/elemental_properties_v1.csv` exists and is used by `descriptor_calculator.py` and `feature_engineering_pipeline.py`. |

## Execution Order and Dependencies

**Phase 1 (Sanity Check — Independent on small manual dataset)**:
T001 → T002 → T003 → T004

**Phase 2 (Full Pipeline — Dependent on Phase 1, runs on aggregated data)**:
T005.A → T005.B → T005.C → T006 → T007 → T008 → T008.C → T009 → T009.D → T010

**Phase 3 (Reporting & Finalization — Dependent on Phase 2)**:
T011 → T012 → T012.B → T013

**Overall Order**: T001 → T002 → T003 → T004 → T005.A → T005.B → T005.C → T006 → T007 → T008 → T008.C → T009 → T009.D → T010 → T011 → T012 → T012.B → T013.

**Note**: T004 runs independently on a small manual dataset (data/raw/manual_curated.csv) to verify the technical path before full data aggregation. T005–T013 run on the full aggregated dataset from T005. This separation allows early detection of technical issues without waiting for full data aggregation. Phase 1 completes before Phase 2 begins.