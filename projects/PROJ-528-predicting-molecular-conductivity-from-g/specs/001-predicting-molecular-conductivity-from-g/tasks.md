# Tasks: Predicting Molecular Conductivity from Graph-Based Features

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and contracts.  
All tasks are expressed as checklist items following the canonical format.  
Checked boxes (`[x]`) indicate work that has already been verified; unchecked
boxes (`[ ]`) denote pending work that must be completed and validated.

---

## Phase 0 – Foundational infrastructure (now fully aligned with the plan)

- [ ] T001 [P] [US1] Establish project skeleton, pinned dependencies, configuration, validators, scaffold‑splitting utilities, and contracts.  
  **Paths**: `code/`, `code/requirements.txt`, `code/validators.py`, `code/split.py`, `specs/001-predicting-molecular-conductivity-from-g/contracts/`.  
  **Verification**:  
  ​  - `requirements.txt` contains exact version pins and installs without errors.  
  ​  - `code/validators.py --validate contracts/*` returns exit 0 for all schemas.  
  ​  - `code/split.py` correctly partitions a toy SMILES set using scaffold IDs.  

- [ ] T010 [P] [US1] Implement comprehensive unit‑test suite for descriptor computation, scaffold leakage prevention, log‑transform, outlier filtering, VIF calculation, Benjamini‑Hochberg correction, and plot generation.  
  **Paths**: `tests/unit/test_descriptors.py`, `tests/unit/test_scaffold.py`, `tests/unit/test_preprocessing.py`, `tests/unit/test_statistics.py`.  
  **Verification**: `pytest -q tests/unit/` runs with all tests passing (exit 0) and coverage ≥ 90 %.  

- [X] T011 [US1] Validate that the target variable (conductivity) spans ≥ 3 orders of magnitude before any modeling.  
  **Paths**: `code/preprocessing.py`, `data/processed/target_dynamic_range.json`.  
  **Verification**: Script aborts with clear error if dynamic range < 3 log10 units; otherwise writes JSON with `min`, `max`, `range_log10`.  

- [ ] T012 [US1] Exclude molecules with missing conductivity or invalid descriptors from training set, logging counts.  
  **Paths**: `code/preprocessing.py`, `data/processed/exclusion_log.json`.  
  **Verification**: Log file contains `missing_conductivity`, `invalid_descriptors` counts; resulting training CSV contains only valid rows.  

- [ ] T013 [P] [US1] Build data‑loading pipeline, strict target‑variable validation, quantum‑proxy reporting, and full RDKit descriptor set generation.  
  **Paths**: `code/data_loader.py`, `code/target_proxy.py`, `data/processed/descriptors.csv`, `data/processed/quantum_proxy_report.json`.  
  **Verification**:  
  ​  - Loading a real PubChem/HMaterials dataset succeeds without fallback to synthetic data.  
  ​  - `descriptors.csv` contains ≥ 10 numeric descriptor columns for every valid molecule and conforms to `contracts/descriptor_schema.schema.yaml`.  
  ​  - `quantum_proxy_report.json` correctly records presence/absence of HOMO‑LUMO data.  

- [X] T014 [US1] Detect presence/absence of quantum‑derived descriptors (e.g., HOMO‑LUMO gap) and log the result.  
  **Paths**: `code/target_proxy.py`, `data/processed/quantum_proxy_report.json`.  
  **Verification**: JSON includes fields `"homo_lumo_present": true/false` and `"fallback_used": true/false`.  

- [ ] T015 [US1 US2] **Empirical target‑proxy fallback** – If both measured conductivity and HOMO‑LUMO gap are missing, compute a topological proxy (linear combination of `aromatic_ring_count` and `conjugation_path_length`) and set `target_type` to `topological_proxy`.  
  **Paths**: `code/target_proxy.py`, `data/processed/descriptors.csv`.  
  **Verification**: When fallback is triggered, `descriptors.csv` contains a non‑null `log_conductivity` column and `quantum_proxy_report.json` records `"fallback_used": true`.  

- [ ] T050 [US1] **CPU‑only verification** – Assert that no CUDA libraries are imported and that `torch.cuda.is_available()` returns false; fail early if GPU dependencies are detected.  
  **Paths**: `code/cpu_check.py`, `data/processed/cpu_check_report.json`.  
  **Verification**: Script exits 0 on CPU‑only runners; writes JSON with `"cpu_only": true`.  

- [ ] T051 [US1] **Random‑seed pinning & recording** – Set a global seed (`SEED = 42`) in a shared module and write all seed values to `state/seeds.json`.  
  **Paths**: `code/seed.py`, `state/seeds.json`.  
  **Verification**: All scripts import `code.seed`; `seeds.json` contains entries for `numpy`, `random`, `torch`, `sklearn`.  

- [ ] T052 [US1] **Pipeline runtime measurement** – Wrap the entire orchestrated run (see T104) with a timer, write elapsed seconds to `data/processed/runtime_report.json`, and assert ≤ 21600 s (6 h).  
  **Paths**: `code/runtime_tracker.py`, `data/processed/runtime_report.json`.  
  **Verification**: CI fails if runtime exceeds 6 h; JSON contains `"elapsed_seconds"` and `"within_budget": true/false`.  

- [ ] T053 [US2] **Baseline R² comparison** – Compute a random‑prediction baseline (R² = 0) and store a JSON comparison (`data/processed/baseline_comparison.json`) showing model R² vs baseline.  
  **Paths**: `code/baseline.py`, `data/processed/baseline_comparison.json`.  
  **Verification**: JSON fields `"model_r2"`, `"baseline_r2"` (0.0), `"improvement"`; validator checks schema.  

- [ ] T054 [US3] **Permutation importance robustness report** – Compare original feature‑importance rankings with permutation importance scores; produce `data/processed/importance_robustness.json` containing correlation between rankings and a pass/fail flag.  
  **Paths**: `code/analysis.py`, `data/processed/importance_robustness.json`.  
  **Verification**: JSON includes `"spearman_corr"` and `"robust": true/false`.  

- [ ] T055 [US3] **Confidence‑interval coverage measurement** – For each correlation plot, compute the proportion of true values falling within the 95 % CI and write `data/processed/ci_coverage.json`.  
  **Paths**: `code/ci_coverage.py`, `data/processed/ci_coverage.json`.  
  **Verification**: JSON contains `"coverage"` (0‑1) and `"target_coverage": 0.95`.  

- [ ] T056 [US1] **Validate `dataset_schema.yaml`** – Run `code/validators.py` against the processed dataset (`data/processed/descriptors.json`) using `contracts/dataset_schema.yaml`.  
  **Paths**: `code/validators.py`, `data/processed/validation_report_dataset.json`.  
  **Verification**: Validator exits 0; report records `"valid": true`.  

- [ ] T057 [US1] **Validate raw input against `input.schema.yaml`** – Ensure `data/raw/input.csv` conforms to the input contract.  
  **Paths**: `code/validators.py`, `data/processed/validation_report_input.json`.  
  **Verification**: Same as T056 but with `input.schema.yaml`.  

- [ ] T058 [US3] **Generate `model_results.json`** conforming to `contracts/model_results_schema.schema.yaml`.  
  **Paths**: `code/model_results.py`, `data/processed/model_results.json`.  
  **Verification**: JSON schema validation passes.  

- [ ] T059 [US1] **Compute and store checksums for all raw and processed data files** – SHA‑256 hashes written to `state/data_checksums.json`.  
  **Paths**: `code/checksum.py`, `state/data_checksums.json`.  
  **Verification**: JSON maps file paths to hash strings; checksum script exits 0.  

## Phase 1 – Descriptor Computation & Target Handling

- [ ] T016 [P] [US1] Compute graph‑based descriptors for each molecule using RDKit (aromaticity, conjugation length, ring count, degree statistics, average path length, etc.).  
  **Paths**: `code/descriptors.py`, `data/processed/descriptors.csv`.  
  **Verification**: `descriptors.csv` contains all required columns, passes `contracts/descriptor_schema.schema.yaml` validation, and logs any computation failures.  

- [ ] T017 [P] [US1] Derive the target variable: log‑transform conductivity when present; otherwise invoke `code/target_proxy.py` to generate a topological proxy and set `target_type` accordingly.  
  **Paths**: `code/target_proxy.py`, `data/processed/descriptors.csv`, `data/processed/quantum_proxy_report.json`.  
  **Verification**: `descriptors.csv` includes a non‑null `log_conductivity` column; `quantum_proxy_report.json` records `"fallback_used": true` when proxy is used.  

- [ ] T018 [P] [US1] Filter out rows with missing or invalid descriptors or targets, producing cleaned training and test CSVs.  
  **Paths**: `code/preprocessing.py`, `data/processed/filtered_train.csv`, `data/processed/filtered_test.csv`.  
  **Verification**: No NaN values remain; exclusion counts are logged in `data/processed/exclusion_log.json`.  

## Phase 1 – Pending work (to be implemented and verified)

- [ ] T100 [P] [US1 US2] **Empirical target‑proxy fallback** – Implement `code/target_proxy.py` that derives a topological proxy for conductivity when both measured conductivity and HOMO‑LUMO gap are missing (e.g., linear combination of `aromatic_ring_count` and `conjugation_path_length`). The pipeline must invoke this automatically, log a warning, and set `target_type` to `topological_proxy`.  
  **Verification**: Run the full pipeline on a dataset lacking conductivity; confirm `descriptors.csv` contains a non‑null `log_conductivity` column and `quantum_proxy_report.json` records `"fallback_used": true`.  

- [ ] T101 [P] [US2 US3] **Model results aggregation** – Create/overwrite `data/processed/model_output.json` to match `contracts/model_output_schema.yaml`. The file must contain a top‑level `runs` array; each entry includes `run_id`, `model_type`, `r2_test`, `mae_test`, `r2_cv_mean`, `r2_cv_std`, `outlier_threshold`, `target_type`, and `vif_excluded_features`.  
  **Verification**: Execute the validation command (see concern) and obtain exit 0.  

- [ ] T102 [P] [US3] **Permutation feature importance** – Add `permutation_feature_importance(model, X, y)` to `code/analysis.py` using `sklearn.inspection.permutation_importance` (`n_repeats=10`, `random_state=SEED`). Write the ranked list to `data/processed/feature_importance.csv` with columns `feature, importance_score`, sorted descending.  
  **Verification**: File exists, header matches exactly, row count equals number of retained (VIF‑filtered) features, and all scores are finite numbers.  

- [ ] T104 **Run‑book reconciliation and pipeline orchestration** – Implement `code/main.py` that orchestrates the full workflow in the exact order: data loading → target validation/fallback → descriptor computation → VIF filtering → scaffold split → circularity check → model training → sensitivity analysis → permutation importance → feature/VIF report → plots → summary generation. Update `docs/quickstart.md` and `plan.md` to reflect the single reproducible command `python -m code.main`.  
  **Verification**: Executing the documented command on a clean runner reproduces every artifact listed in T103 without errors and finishes within the 6‑hour CPU budget.  

- [ ] T103 **Contract validation of all result artifacts** – Run `code/validators.py --validate <file> --schema <schema>` for each downstream artifact:  
  * `data/processed/descriptors.csv` vs `contracts/descriptor_schema.schema.yaml`  
  * `data/processed/model_output.json` vs `contracts/model_output_schema.yaml`  
  * `data/processed/feature_vif_report.json` vs `contracts/feature_schema.yaml`  
  * `data/processed/analysis_summary.json` vs a newly added `contracts/analysis_summary_schema.yaml`  
  * `data/processed/sensitivity_analysis.json` vs `contracts/sensitivity_schema.schema.yaml`  
  Record each command and its exit code in `docs/validation_results.md`.  
  **Verification**: All validator invocations exit 0; `validation_results.md` lists the six commands and their success.  

- [ ] T046 **Quick‑start end‑to‑end verification** – Run the quick‑start command (`python -m code.main`) on a fresh runner and assert that every artifact from T104 is produced and all unit‑test suites pass. Log the overall success/failure in `docs/quickstart_validation.json`.  
  **Verification**: JSON contains `"quickstart_passed": true` and timestamps; CI fails if any artifact is missing or a test fails.  

- [ ] T105 [P] **Methods & results summary document** – Write `docs/results_summary.md` that concisely reports: final R², MAE, CV statistics for both models; target type used; list of VIF‑excluded features; BH‑adjusted p‑values; family‑wise error rate; sensitivity‑analysis R² variance; CI‑coverage; and references to the resonance‑descriptor plots. Every numeric claim must be programmatically extracted from the corresponding JSON/CSV artifact (e.g., using a small helper script).  
  **Verification**: A sanity‑check script confirms that each number in `results_summary.md` matches the value in its source file (exit 0).  

- [ ] T106 [P] **Full re‑run and paper‑stage handoff** – In a fresh environment, execute the quick‑start workflow, confirm all unit tests and T103 validations pass, and compile `docs/paper_handoff.md` that lists all generated figures, result tables, limitation statements, and a brief note on the deferred Hückel‑energy analysis.  
  **Verification**: The handoff document is present, the end‑to‑end run completes in ≤ 6 hours, and the CI logs report zero failures.  

- [ ] T107 [P] **Family‑wise error rate (FWER) measurement** – After Benjamini‑Hochberg correction, compute the proportion of features with `adjusted_p_value < 0.05`. Write the scalar to `data/processed/fwer_report.json` (`{"alpha": 0.05, "fwer": <value>}`) and cite it in `results_summary.md`.  
  **Verification**: JSON file exists, `0 ≤ fwer ≤ 1`, and a line in `results_summary.md` reads “Family‑wise error rate (α = 0.05): <value>”.  

- [ ] T108 [P] **Feature/VIF JSON report** – Generate `data/processed/feature_vif_report.json` conforming to `contracts/feature_schema.yaml`. For each retained descriptor include `feature_name`, `importance_score` (from permutation importance), `vif_score`, and `is_excluded`. Add a `summary` block with `total_features`, `excluded_features`, and `max_vif`.  
  **Verification**: `jsonschema` validation succeeds; the number of entries equals the number of retained features; `summary.max_vif` matches the highest `vif_score` in the list.  

- [ ] T109 [P] **Circularity (residual‑variance) check** – Implement `code/circularity_check.py` that fits a linear model of the target against all retained descriptors and computes the explained variance (R²). If R² > 0.95, abort with a clear error indicating circularity. Record the outcome in `data/processed/circularity_check.json` (`{"passed": true}` or `{"passed": false, "r2": <value>}`).  
  **Verification**: When the pipeline runs on a dataset that would trigger circularity, it aborts with the prescribed error message; otherwise `circularity_check.json` contains `"passed": true`.  

- [ ] T119 [P] **Data‑model entity: Molecule** – Generate a canonical JSON array `data/processed/molecules.json` matching the `Molecule` entity schema (smiles, molecular_weight, log_conductivity, is_valid, scaffold_id).  
  **Verification**: JSON validates against `contracts/dataset_schema.yaml` and contains `minItems: 1`.  

- [ ] T120 [P] **Data‑model entity: Descriptor** – Produce `data/processed/descriptors_full.json` where each entry follows the `Descriptor` schema (aromaticity_index, conjugation_length, etc.).  
  **Verification**: Validation against `contracts/descriptor.schema.yaml` succeeds.  

- [ ] T121 [P] **Data‑model entity: ModelResult** – Output `data/processed/model_result.json` adhering to the `ModelResult` definition (model_type, r2_test, mae_test, cv_r2_mean, cv_r2_std, feature_importance).  
  **Verification**: JSON conforms to `contracts/model_output_schema.yaml`.  

## Phase 2 – Preprocessing & Splitting (expanded)

- [ ] T019 [P] [US3] Calculate VIF for all predictors; exclude features with VIF > 10.  
  **Verification**: `feature_vif_report.json` lists excluded features; no retained feature has `vif_score` > 10.  

- [ ] T020 [P] [US2] Perform scaffold splitting (a standard train‑test split). **Mitigation**: If test set < 20 molecules, retry with new seed. If N < 100 total, enable Nested CV.  
  **Verification**: `train.csv` and `test.csv` contain the expected number of rows; seed used is recorded in `state/seeds.json`.  

- [ ] T021 [P] [US2] **Split retry logic** – If the scaffold split yields a test set with fewer than 100 molecules, automatically reseed and repeat up to three times; abort with an informative error if still insufficient.  
  **Verification**: Log `split_retry.log` records attempts; final split meets size requirement.  

## Phase 3 – Model Training & Evaluation (expanded)

- [ ] T022 [P] **Circularity pre‑check** – Run `code/circularity_check.py` before any model training (now positioned before T027).  
  **Verification**: Pipeline aborts early if circularity detected.  

- [ ] T023 [P] Train Random Forest and Gradient Boosting models on log‑transformed conductivity.  
  **Verification**: `model_output.json` contains entries for both model types with training metrics.  

- [ ] T024 [P] Evaluate models (R², MAE, CV). **Mitigation**: If N < 100, use Nested CV and Bootstrap (sufficient iterations).  
  **Verification**: CV statistics recorded in `model_output.json`.  

- [ ] T025 [P] Perform sensitivity analysis (Kruskal‑Wallis H‑test) across outlier thresholds {2.5σ, 3.0σ, 3.5σ}.  
  **Verification**: `sensitivity_results.json` includes `thresholds`, `r2_scores`, `mae_scores`, `variance_r2`.  

- [ ] T026 [P] Apply Benjamini‑Hochberg correction to p‑values from feature‑target correlations.  
  **Verification**: `analysis_summary.json` contains `fdr_adjusted_pvalues`.  

- [ ] T027 [P] **Scaffold split, training, CV, sensitivity** – (historical; retained for completeness).  

- [ ] T028 [P] **Correlation plots & CI** – Generate PNG images for top‑5 features with 95 % confidence intervals; store in `figures/`.  
  **Verification**: Images are viewable, contain axis labels, regression line, shaded CI.  

- [ ] T039 [P] **VIF exclusion & retraining** – (now covered by T019/T021/T108).  

- [ ] T040 [P] **Feature‑importance & analysis summary** – (now covered by T054, T055, T107).  

## Phase 4 – Reporting

- [ ] T029 [P] Generate final report `docs/results_summary.md` (see T105).  
- [ ] T030 [P] Validate all outputs against contracts (see T103).  

## Phase 8 – Deferred Analysis (Blocked)

- [ ] T061 [DEFERRED] Hückel Energy Computation. **Blocked** until external dataset with Hückel energy data is found.  
- [ ] T012b [DEFERRED] Unit Test for Hückel Resonance. **Blocked** until T061 is complete or external data is available.  

---  

### Notes on Parallelism Tags

- Tasks that write or overwrite shared artifacts (e.g., T104, T103, T108) have **no** `[P]` tag to enforce sequential execution.
- Pure validation or checksum tasks (e.g., T050, T051, T052, T059) retain `[P]` where they do not interfere with other writes.