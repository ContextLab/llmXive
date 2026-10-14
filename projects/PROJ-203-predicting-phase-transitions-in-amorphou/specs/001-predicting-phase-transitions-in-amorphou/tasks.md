# Tasks: Predicting Phase Transitions in Amorphous Solids Using Machine Learning  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  

The checklist below follows the canonical format `- [ ] T### [P?] [USx?] description …` with indented continuation lines that state the exact file path, the requirement it satisfies, and an observable verification step.

---

## Phase 0 – Scope alignment & specification sanity  

| Goal: Ensure the plan reflects the compute‑budget limitation (pilot N=24) while keeping the original specification untouched. |
|------|

- [ ] **T001** [US1] Verify that `plan.md` contains a “Critical Scope Resolution” section documenting the reduction to 24 compositions.  
  - **Path**: `plan.md`  
  - **Requirement**: The plan must explicitly state the pilot‑study exception.  
  - **Verification**: Grep “Critical Scope Resolution” and confirm the text mentions *N = 24*.

- [ ] **T002** [US1] Edit `plan.md` to add the “Critical Scope Resolution” paragraph and update the “Success Criteria” section to note that RMSE/ROC‑AUC targets are evaluated via null‑model and permutation tests on the pilot set.  
  - **Path**: `plan.md` (in‑place edit)  
  - **Requirement**: The plan must be consistent with the spec’s FR‑001 while acknowledging the compute constraint.  
  - **Verification**: Re‑run the check from **T001**; it must now succeed.

---

## Phase 1 – Project scaffolding (completed)  

| Goal: Create a reproducible directory layout and core utilities that all later tasks depend on. |
|------|

- [ ] **T003**  Initialise project directories (`data/raw/`, `data/processed/`, `data/logs/`, `code/`, `code/data/`, `code/models/`, `code/utils/`, `artifacts/models/`, `artifacts/figures/`, `artifacts/reports/`, `tests/`, `docs/`).  
  - **Path**: filesystem (created by script `code/setup_structure.py`).  
  - **Verification**: `tree` output contains all listed folders.

- [ ] **T004**  Create `code/requirements.txt` with pinned versions of all scientific packages required by the spec (e.g., `numpy`, `pandas`, `scikit-learn`, `shap`, `mdtraj`, `lammps`, `datasets`, `pyyaml`).  
  - **Path**: `code/requirements.txt`  
  - **Verification**: `pip install -r code/requirements.txt` completes without errors.

- [ ] **T005**  Implement `code/config.py` – a thin dataclass exposing paths, random seeds, simulation parameters (cooling rate, MD step limits), and enum definitions for `Family`.  
  - **Path**: `code/config.py`  
  - **Verification**: Importing `code.config` succeeds and `Config().data_raw` points to `data/raw/`.

- [ ] **T006**  Implement `code/utils/validators.py` with functions `check_nan(df)`, `check_physical_bounds(descriptor_row)`.  
  - **Path**: `code/utils/validators.py`  
  - **Verification**: Unit test in `tests/unit/test_validators.py` passes.

- [ ] **T007**  Implement `code/utils/logging_config.py` that creates a logger writing to `data/logs/pipeline.log` with timestamps and log‑level INFO.  
  - **Path**: `code/utils/logging_config.py`  
  - **Verification**: After calling `setup_logger()`, a test log entry appears in the file.

- [ ] **T008**  Implement `code/utils/timeout_enforcer.py` – a context manager `PipelineTimeout(hours=6)` that raises `TimeoutError` if the wrapped block exceeds the wall‑clock limit.  
  - **Path**: `code/utils/timeout_enforcer.py`  
  - **Verification**: A small script deliberately sleeping >6 h triggers the exception (tested with a 1‑second timeout for speed).

---

## Phase 2 – Data pipeline & descriptor generation (pilot N = 24)  

| Goal: Produce a validated, fully‑featured dataset (`final_dataset.parquet`) that satisfies FR‑001, FR‑002, and FR‑008. |
|------|

- [ ] **T009** [US1] Validate the presence and integrity of `data/raw/literature_subset.csv`.  
  - **Path**: `code/data/validate_literature_subset.py` → checksums `data/raw/literature_subset.csv`.  
  - **Verification**: Script exits with code 0; missing or corrupted file raises `FileNotFoundError` and aborts the run.

- [ ] **T010** [US1] Run MD simulations for each pilot composition (`data/raw/pilot_compositions.csv`) using LAMMPS (via `pylammps`). Enforce a 30‑minute CPU cap per composition; if exceeded, truncate to the final 500 steps and flag `simulation_status="truncated"` in metadata.  
  - **Path**: `code/data/run_md_sim.py` → outputs trajectories to `data/raw/md_trajectories/` and a log file `data/logs/simulation_times.json`.  
  - **Verification**: All 24 entries in `simulation_times.json` have `status` in {`complete`,`truncated`,`failed`} and no entry exceeds 1800 s.

- [ ] **T011** [US1] Extract structural descriptors (RDF peak position/width, bond‑angle variance, coordination number) from each trajectory.  
  - **Path**: `code/data/extract_descriptors.py` → writes `data/processed/descriptors.csv`.  
  - **Verification**: Row count equals number of successful or truncated simulations; no NaN values in descriptor columns.

- [ ] **T012** [US1] Record the MD cooling rate for each run and store it in `data/processed/cooling_rates.csv`.  
  - **Path**: Same script as **T011** (adds a column `cooling_rate_K_min`).  
  - **Verification**: All rates are positive floats; summary statistics printed to log.

- [ ] **T013** [US1] Implement the timescale‑matching protocol (FR‑008). For each composition, read the experimental DSC cooling rate from `literature_subset.csv`, compute scaling factor `S = dsc_rate / md_rate`, and write a metadata file `data/processed/timescale_metadata.json` containing `md_cooling_rate`, `dsc_cooling_rate`, `scaling_factor`, `alignment_applied=true`, `SRO_Invariance_Assumed=true`.  
  - **Path**: `code/data/timescale_match.py`.  
  - **Verification**: JSON contains one entry per composition and the flag `alignment_applied` is true.

- [ ] **T014** [US1] Merge descriptors, cooling‑rate metadata, and experimental Tg/Tx into a single dataframe (`data/processed/merged_raw.parquet`). Do **not** create the crystallization label yet.  
  - **Path**: `code/data/merge_raw.py`.  
  - **Verification**: Parquet file has columns `{composition_id, rdf_peak_position, rdf_peak_width, bond_angle_variance, coordination_number, cooling_rate, Tg, Tx}` and row count = 24 – (#failed simulations).

- [ ] **T015** [US1] Apply crystallization labeling (FR‑002) and exclude rows with missing Tg, Tx, or failed simulations.  
  - **Logic**: `label = 1 if abs(Tx‑Tg) ≤ 50 K else 0`.  
  - **Path**: `code/data/label_and_filter.py` → outputs `data/processed/final_dataset.parquet` and a log `data/logs/excluded_rows.log`.  
  - **Verification**: Log file lists any excluded composition IDs; the final parquet contains no nulls in required predictor columns and includes a `crystallization_label` column.

- [ ] **T016‑PKG** [US1] Package the validated `final_dataset.parquet` into a versioned archive `artifacts/datasets/final_dataset_v1.zip` and emit a manifest `artifacts/datasets/manifest.json`.  
  - **Path**: `code/data/package_dataset.py`.  
  - **Verification**: Archive exists, manifest lists the parquet file with checksum, and schema validation (see T016) passes.

- [ ] **T016** [US1] Run a schema validation against `specs/001-predicting-phase-transitions/contracts/dataset.schema.yaml` to certify that `final_dataset.parquet` conforms to the contract.  
  - **Path**: `code/utils/schema_validator.py`.  
  - **Verification**: Validation script exits with code 0; any schema violation raises an exception and halts the pipeline.

---

## Phase 3 – Model training & performance validation (US 2)  

| Goal: Train Random‑Forest models, evaluate against the null baseline, and satisfy FR‑003, FR‑006, and SC‑001/SC‑002. |
|------|

- [ ] **T017** [US2] Load `final_dataset.parquet`, perform a stratified (by `family`) train‑test split (80 %/20 %). Verify that each family is represented proportionally in both splits.  
  - **Path**: `code/models/data_split.py` → creates `data/processed/train_set.parquet` and `data/processed/test_set.parquet`.  
  - **Verification**: Print class‑distribution tables; unit test `tests/integration/test_split.py` asserts exact family counts.

- [ ] **T018** [US2] Train a Random‑Forest regressor for Tg and a Random‑Forest classifier for crystallization using `sklearn`. Use a limited grid search (max 30 models) that completes within 2 h. Save models to `artifacts/models/tg_regressor.pkl` and `artifacts/models/crystallization_classifier.pkl`.  
  - **Path**: `code/models/train_rf.py`.  
  - **Verification**: Model files exist; training log reports total runtime < 2 h.

- [ ] **T019** [US2] Evaluate model performance on the held‑out test set: compute RMSE for Tg, ROC‑AUC for classification, and 5‑fold CV scores. Compare RMSE to the null‑model RMSE (mean predictor) and record both in `artifacts/reports/metrics.json`. Fail the pipeline if `roc_auc <= 0.7`.  
  - **Path**: `code/models/evaluate.py`.  
  - **Verification**: `metrics.json` contains keys `rmse`, `null_model_rmse`, `roc_auc`, `cv_scores`; pipeline aborts with error if `roc_auc` ≤ 0.7.

- [ ] **T020** [US2] Perform a sensitivity analysis on the crystallization threshold (FR‑006). Iterate thresholds from 25 K to 100 K in 5 K steps, compute balanced accuracy, false‑positive rate, and class balance for each. Save results to `artifacts/reports/sensitivity_report.json`. Flag the threshold as “unstable” if FPR varies > 10 % across the range.  
  - **Path**: `code/models/sensitivity.py`.  
  - **Verification**: JSON contains entries with fields `threshold`, `balanced_accuracy`, `fpr`, `class_balance`, and a top‑level boolean `unstable`.

- [ ] **T021** [US2] Aggregate wall‑clock timings from `data/logs/simulation_times.json`, training logs, and any other timed sections. Verify total pipeline time ≤ 6 h (SC‑005) and write `artifacts/reports/pipeline_timing.json`.  
  - **Path**: `code/utils/timing_aggregator.py`.  
  - **Verification**: `pipeline_timing.json` has field `total_seconds`; CI step fails if > 21600 s.

---

## Phase 4 – Interpretability, statistical rigor & cross‑family analysis (US 3)  

| Goal: Produce SHAP explanations, correct for multiple comparisons, diagnose collinearity, and generate the final interpretability report (FR‑004, FR‑005, FR‑007, FR‑008). |
|------|

- [ ] **T022** [US3] Compute SHAP values for both the regression and classification models, stratified by chemical family. Store raw SHAP arrays in `artifacts/reports/shap_values_{family}.npy` and a ranked importance list (`shap_rank_{family}.json`).  
  - **Path**: `code/models/shap_compute.py`.  
  - **Verification**: Files exist for `oxide`, `sulfide`, and `organic`; each JSON contains at least the top 10 features.

- [ ] **T023** [US3] Generate SHAP summary plots and partial‑dependence plots (PDP) for the top‑3 descriptors per family. Save PNGs to `artifacts/figures/shap_summary_{family}.png` and `artifacts/figures/pdp_{family}_{feature}.png`.  
  - **Path**: `code/models/visualize_shap.py`.  
  - **Verification**: All expected image files are present and non‑empty (size > 10 KB).

- [ ] **T024** [US3] Apply a Bonferroni (or FDR) correction to the family‑wise SHAP importance comparisons (FR‑005). Output `artifacts/reports/multiple_comparison.json` with corrected p‑values for each pairwise family comparison.  
  - **Path**: `code/models/multiple_comparison.py`.  
  - **Verification**: JSON includes keys `comparison_pair`, `p_value`, `corrected_p_value`.

- [ ] **T025** [US3] Compute Variance‑Inflation‑Factor (VIF) diagnostics for all predictors (FR‑007). Store results in `artifacts/reports/collinearity_report.json` and a summary table `artifacts/reports/collinearity_summary.txt`.  
  - **Path**: `code/models/collinearity.py`.  
  - **Verification**: No VIF > 5, or if any exceed, the report flags them and the pipeline records a warning.

- [ ] **T026** [US3] Assemble an interpretability report (`docs/reports/interpretability_report.md`) that:  
  1. Lists universal predictors (features with significant SHAP importance across all families).  
  2. Highlights family‑specific drivers.  
  3. Includes the corrected p‑values, VIF summary, and sensitivity‑analysis findings.  
  4. Explicitly notes any assumptions (e.g., “SRO invariance assumed”).  
  - **Verification**: Markdown file contains the four sections, links to all generated figures/tables, and a post‑validation step (`code/docs/validate_links.py`) confirms each linked file exists.

- [ ] **T026‑VAL** [US3] Helper script invoked by T026 to verify that every markdown link in `interpretability_report.md` points to an existing file on disk.  
  - **Path**: `code/docs/validate_links.py`.  
  - **Verification**: Script exits with code 0; any broken link causes pipeline failure.

- [ ] **T027** [US3] Compute confidence intervals for SHAP importance of the top‑3 descriptors per family using bootstrap resampling (1,000 replicates). Store CI data in `artifacts/reports/shap_ci_{family}.json`.  
  - **Path**: `code/models/shap_bootstrap_ci.py`.  
  - **Verification**: JSON includes `feature`, `mean_importance`, `ci_lower`, `ci_upper` for each top‑3 descriptor; CI width is reported.

- [ ] **T028** [US3] Perform a null‑model and permutation test (FR‑004 extension). Train a mean‑predictor baseline, shuffle target labels 1,000 times, compute RMSE distribution, and record the permutation p‑value in `artifacts/reports/permutation_test.json`.  
  - **Path**: `code/models/null_permutation.py`.  
  - **Verification**: JSON contains `null_model_rmse`, `permutation_p_value`, and boolean `is_significant` (p < 0.05).

- [ ] **T029** [US3] Validate the sensitivity analysis report against `specs/001-predicting-phase-transitions/contracts/sensitivity.schema.yaml`.  
  - **Path**: `code/utils/validate_sensitivity_schema.py`.  
  - **Verification**: Script exits with code 0; any schema violation aborts the pipeline.

---

## Phase 5 – End‑to‑end reproducibility hand‑off (US 0)  

| Goal: Verify that a fresh checkout can reproduce the complete pipeline and that all contractual schemas are satisfied. |
|------|

- [ ] **T030** [US0] Provide a `quickstart.md` that documents the single command to run the full pipeline (`python -m code.main`). The command must internally use `PipelineTimeout` and abort with a clear error if any step fails.  
  - **Path**: `docs/quickstart.md`.  
  - **Verification**: Running the command on a clean runner produces `final_dataset.parquet`, model files, and all report artifacts without manual intervention.

- [ ] **T031** [US0] Execute the end‑to‑end pipeline on the CI runner and assert that:  
  1. All schema validations (`dataset.schema.yaml`, `output.schema.yaml`) pass.  
  2. Total wall‑clock time ≤ 6 h.  
  3. All required output files exist (`final_dataset.parquet`, model `.pkl`s, SHAP artifacts, reports, etc.).  
  - **Path**: CI workflow uses script `code/main.py`.  
  - **Verification**: CI job checks for the existence of each listed file, runs both schema validators, and fails if any file is missing or any validation returns non‑zero exit status.

---

## Phase 6 – Full‑scale dataset generation (FR‑001 compliance)  

| Goal: Extend the pipeline to meet the original specification of ≥ 500 valid compositions. |
|------|

- [ ] **T037** [US1] Design a scalable, chunk‑based execution framework (`code/data/scale_pipeline.py`) that partitions a list of up to 500 compositions into batches respecting the 30‑minute per‑composition cap and the overall 6‑hour wall‑clock limit (e.g., 5 batches of 100 compositions run sequentially). Document the batching logic and required compute resources.  
  - **Path**: `code/data/scale_pipeline.py`.  
  - **Verification**: Script prints batch plan, total estimated runtime ≤ 6 h per batch, and writes a `batch_plan.json`.

- [ ] **T038** [US1] Run the scalable pipeline on the full 500‑composition list (`data/raw/full_compositions.csv`), generate descriptors, apply timescale matching, label, and produce a consolidated `data/processed/full_dataset.parquet`. Validate against `dataset.schema.yaml` and archive as `artifacts/datasets/full_dataset_v1.zip`.  
  - **Path**: `code/data/run_full_scale.py`.  
  - **Verification**: Parquet file contains ≥ 500 rows with required fields, schema validation passes, and archive/manifest are created.

- [ ] **T039** [US1] Document the power‑analysis and limitation discussion for the pilot vs. full dataset in `docs/power_analysis.md`, citing why the pilot is acceptable for method development and how the full dataset will be used for final claims.  
  - **Path**: `docs/power_analysis.md`.  
  - **Verification**: File exists and includes sections on sample size, expected RMSE variance, and statistical power.
