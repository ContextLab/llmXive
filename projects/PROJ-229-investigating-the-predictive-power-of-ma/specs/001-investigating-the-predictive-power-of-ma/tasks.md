---
description: "Task list for feature implementation"
---

# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Input**: Design documents from `/specs/001-investigating-the-predictive-power-of-ma/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001_init_structure [P] Create data directories (`data/raw`, `data/processed`, `data/results`, `data/external`), code directories (`code/data`, `code/models`, `code/utils`, `code/validate`), and test directories (`tests/unit`, `tests/integration`, `tests/contract`). Verify existence via `tests/unit/test_directories.py`. **Deliverable**: Directories exist; `tests/unit/test_directories.py`.
- [X] T002 Initialize Python project with `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml`, `mp-api`, `datasets` dependencies. **Deliverable**: `requirements.txt` pinning all versions.
- [X] T003 [P] Configure linting and formatting in `pyproject.toml`: Add `[tool.black]`, `[tool.isort]`, and `[tool.flake8]` sections with standard project settings (`max-line-length = 88`). **Deliverable**: `pyproject.toml`.
- [X] T044 Implement global random‑seed helper (`code/utils/random_seed.py`) and ensure all scripts import and set the seed from `config.yaml`. **Deliverable**: `code/utils/random_seed.py` and updated scripts.
- [X] T044_test [P] Unit test verifying that importing `random_seed` sets the global seed to the value defined in `config.yaml`. **Deliverable**: `tests/unit/test_random_seed.py`.
- [X] T044a [P] Audit all Python scripts in `code/` to confirm they import `code/utils/random_seed.py` and invoke `set_global_seed()`. **Deliverable**: `tests/unit/test_seed_audit.py`.
- [X] T044b [P] CI task that fails if any new script added to `code/` does not contain the seed import line. **Deliverable**: `tests/unit/test_new_script_seed.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Hygiene, Fallback Logic, and Streaming.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `config.yaml` for API keys, random seeds, time/memory constraints, `top_n` (default: 10), and `similarity_threshold` (default: 0.3). **Deliverable**: `config.yaml`.
- [X] T005 [P] Implement basic logging infrastructure (`code/utils/logger.py`) and error handling in `code/utils/`. **Deliverable**: `code/utils/logger.py`.
- [X] T005d [P] Add unit test for logger (`tests/unit/test_logger.py`) that writes and reads a log entry. **Deliverable**: `tests/unit/test_logger.py`.
- [X] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring. **Constraint**: Dedicated to numerical stability only; no sensitivity analysis logic. **Deliverable**: `code/utils/stability_checks.py`.
- [X] T086_streaming_data_fetch [P] [US1] Implement streaming data fetch in `code/data/fetch_materials.py` using `datasets.load_dataset(..., streaming=True)` to process the full Materials Project dataset in chunks, ensuring memory usage stays below 7 GB. **Dependency**: None (runs first in Phase 2). **Deliverable**: `code/data/fetch_materials.py` (updated).
- [X] T087_streaming_test [P] Unit test verifying that the streaming fetcher processes data in chunks and never exceeds the 7 GB memory limit. **Dependency**: T086. **Deliverable**: `tests/unit/test_streaming_fetch.py`.
- [X] T070_setup [P] Refactor `fetch_materials.py` to REMOVE *synthetic* fallbacks. Replace any `try/except` block that generates `generate_synthetic_*()` data with a strict `raise` on API failure. Preserve the fallback to verified `matbench` dataset on API failure/rate‑limit as required by FR-001. **Constraint**: Must log fallback and continue for real sources; fail loudly for synthetic. **Dependency**: T086. **Deliverable**: `code/data/fetch_materials.py`.
- [X] T070_test [P] Unit test ensuring `fetch_materials.py` raises on API failure and does not produce synthetic data. **Dependency**: T070_setup. **Deliverable**: `tests/unit/test_fetch_strict.py`.
- [X] T033 [P] [US1] Implement `code/data/fetch_materials.py` with robust fallback to verified `matbench` dataset on API failure/rate‑limit. **Constraint**: Must log fallback and continue. **Dependency**: T086, T070_setup. **Deliverable**: `code/data/fetch_materials.py`.
- [X] T005a [P] Execute `code/data/fetch_materials.py` to fetch data. **Dependency**: T033, T004, T070_setup, T086. **Constraint**: Verify output exists, row count >= 5000, and checksum matches. **Deliverable**: `data/raw/materials_project_data.json`.
- [X] T005a_run [P] Run T005a and assert successful fetch (log status). **Dependency**: T005a. **Deliverable**: `tests/integration/test_fetch_materials.py`.
- [X] T034 [P] [US1] Implement `code/data/fetch_nist_data.py` with fallback to `melting_point` target if NIST overlap < 500. **Constraint**: Must flag fallback in `target_decision.json`. **Deliverable**: `code/data/fetch_nist_data.py`.
- [X] T005b [P] Execute `code/data/fetch_nist_data.py` to fetch NIST data. **Dependency**: T034, T004. **Constraint**: Verify output exists, row count >= 500, and checksum matches. **Deliverable**: `data/raw/nist_data.json`.
- [X] T005b_run [P] Run T005b and assert successful fetch. **Dependency**: T005b. **Deliverable**: `tests/integration/test_fetch_nist.py`.
- [X] T080_create_target_decision_schema [P] Define JSON schema for `target_decision.json` and `imputation_rate_report.json` and write them to `contracts/target_decision.schema.yaml`. **Deliverable**: `contracts/target_decision.schema.yaml`.
- [X] T005c [P] Implement `code/data/target_consistency_check.py` to compute correlation, decide target, write `data/results/target_decision.json` AND `data/results/imputation_rate_report.json`. **Dependency**: T005a, T005b. **Constraint**: Must generate `imputation_rate_report.json` with fields `imputation_rate`, `proxy_correlation`, and `fallback_flag`. Fallback if overlap < 500. Must explicitly flag limitation if NIST overlap is low. **Deliverable**: `code/data/target_consistency_check.py`, `data/results/target_decision.json`, `data/results/imputation_rate_report.json`.
- [X] T081_implement_target_consistency_check [P] Add the core logic inside `target_consistency_check.py` (computations, decision rules) before the unit test runs. **Dependency**: T005c.
- [X] T005c_run [P] Execute target consistency check and validate output against schema. **Dependency**: T005c. **Deliverable**: `tests/unit/test_target_consistency.py`.
- [X] T006b [P] Define JSON schema for `target_decision.json` (`contracts/target_decision.schema.yaml`). **Deliverable**: `contracts/target_decision.schema.yaml`.
- [X] T006b_schema_test [P] Contract test validating `target_decision.json` against its schema. **Dependency**: T006b. **Deliverable**: `tests/contract/test_target_decision_schema.py`.
- [X] T006c [P] Define JSON schema for `fallback_decision.json` (`contracts/fallback_decision.schema.yaml`). **Dependency**: T006b (schema definition task). **Deliverable**: `contracts/fallback_decision.schema.yaml`.
- [X] T006c_schema_test [P] Contract test for `fallback_decision.json`. **Deliverable**: `tests/contract/test_fallback_schema.py`.
- [X] T006a [P] Verify existence of `data/results/target_decision.json`. **Dependency**: T005c, T006b_schema_test. **Deliverable**: `data/results/target_decision.json`.
- [X] T013 [P] Implement `code/data/fetch_literature_pcm.py`: Fetch known PCMs from `matbench/literature_pcm_validation_set`. **Deliverable**: `code/data/fetch_literature_pcm.py`, `data/external/literature_pcms_raw.csv`.
- [X] T013_fetch_test [P] Contract test confirming fetch succeeded and CSV integrity. **Deliverable**: `tests/contract/test_literature_fetch.py`.
- [X] T013a [P] Implement `code/data/map_literature_pcm.py`: Map literature PCMs to MP IDs. **Dependency**: T013. **Deliverable**: `code/data/map_literature_pcm.py`, `data/external/literature_pcms_mapped.csv`.
- [X] T023 [P] External validation (`code/validate/validate_external.py`) → updates `research.md` with ranking accuracy and produces `validation_report.json`. **Dependency**: T005c, T013a, T023a, T074_core, T073_diag. **Constraint**: Must run regardless of similarity score; log warning if similarity < threshold. **Deliverable**: `code/validate/validate_external.py`, `validation_report.json`.
- [X] T023_test [P] Integration test ensuring `validate_external.py` runs and produces `validation_report.json` with required fields. **Dependency**: T023. **Deliverable**: `tests/integration/test_external_validation.py`.
- [X] T075_orchestrator [P] Update `code/main.py` execution order to: Fetch -> Stream/Process -> VIF -> Train -> **Chemical Similarity Check (Diagnostic)** -> External Validation -> Sensitivity. Ensure `check_chemical_similarity.py` runs before `validate_external.py`. **Dependency**: T015, T073_diag. **Deliverable**: `code/main.py`.
- [X] T075_test [P] CI/integration test that runs the pipeline and checks that the new order is respected and does not break downstream tasks. **Dependency**: T075_orchestrator. **Deliverable**: `tests/integration/test_orchestrator_order.py`.
- [X] T012_compute_descriptors [P] [US1] Implement `code/data/compute_descriptors.py` to compute two distinct feature sets: (1) elemental descriptors (atomic number, electronegativity, radius) and (2) crystal graph representations using `pymatgen`'s `StructureGraph`. **Dependency**: T005a, T005b. **Deliverable**: `code/data/compute_descriptors.py`, `data/processed/features.csv`.
- [X] T012_impl [P] Implement core logic in `code/data/compute_descriptors.py`: Call `pymatgen.analysis.graphs.StructureGraph` for graph features and compute elemental descriptors using `pymatgen.core.periodic_table.Element` properties. **Dependency**: T012_compute_descriptors. **Deliverable**: `code/data/compute_descriptors.py` (logic implemented).
- [X] T012_test [P] Unit test verifying `compute_descriptors.py` produces correct graph structures and elemental features. **Dependency**: T012_impl. **Deliverable**: `tests/unit/test_compute_descriptors.py`.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve curated Materials Project subset, compute descriptors, prepare dataset within 7 GB RAM.

- [X] T009 [P] Contract test for dataset schema (`tests/contract/test_dataset_schema.py`). **Depends on** T012.
- [X] T015 [P] [US1] Assemble final dataset by merging `materials_project_data.json`, `nist_data.json`, and `features.csv`. **Dependency**: T005a, T005b, T012. **Deliverable**: `data/processed/final_dataset.csv`.
- [X] T030c [P] Implement Pearson correlation analysis in `code/evaluate.py`; output `data/results/correlation_report.json` with keys `pearson_r` and `p_value`. **Constraint**: Do NOT enforce a hard pass condition. **Depends on** T015. **Deliverable**: `code/evaluate.py`, `data/results/correlation_report.json`.
- [X] T082_implement_correlation_analysis [P] Write the actual correlation computation logic before the unit test runs. **Dependency**: T030c.
- [X] T030c_report_schema_test [P] Validate JSON schema of `correlation_report.json`. **Deliverable**: `tests/unit/test_correlation_report_schema.py`.
- [X] T030d Add unit test `tests/unit/test_correlation_analysis.py` to assert report exists and fields are numeric. **Depends on** T030c.
- [X] T061_define_correlation_threshold [P] Add `correlation_threshold: a low threshold indicating a modest positive correlation` to `config.yaml`. **Deliverable**: updated `config.yaml`.
- [X] T061_correlation_threshold_test [P] Unit test that asserts `pearson_r` from `correlation_report.json` meets or exceeds `config.yaml` threshold. **Deliverable**: `tests/unit/test_correlation_threshold.py`.
- [X] T041 [P] Unit test (`tests/unit/test_preprocessed_dataset.py`) that verifies the final CSV contains ≥ 5,000 rows with non‑null melting‑point, latent‑heat (where available), all feature columns, and that peak memory usage ≤ 7 GB (using `psutil`). **Depends on** T015.
- [X] T041_memory_assertion [P] Added explicit memory‑usage check in T041 (≤ 7 GB). **Deliverable**: same test file updated.

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train RF, GB, SHAP, and PySR models on CPU within time limits; achieve R² > 0.0.

- [X] T017a [P] `code/models/train_random_forest.py` → `data/models/rf_model.pkl`; logs R² and execution time; continues if R² ≤ 0.0 but flags limitation. **Deliverable**: `data/models/rf_model.pkl`, `data/results/baseline_metrics.json`.
- [X] T017b [P] `code/models/train_gradient_boosting.py` → `data/models/gb_model.pkl`; logs R² and execution time; continues if R² ≤ 0.0 but flags limitation. **Deliverable**: `data/models/gb_model.pkl`, `data/results/baseline_metrics.json`.
- [X] T017c [P] `code/models/verify_baseline_metrics.py` → `data/results/baseline_verification.json`. **Constraint**: Output must include `mean_r2`, `std_r2`, and `t_test_params` (alpha=0.05, two-tailed). **Deliverable**: `data/results/baseline_verification.json`.
- [X] T017d [P] `code/models/train_shap_analysis.py` → `data/models/shap_summary.json`. **Dependency**: T017a, T017b. **Deliverable**: `data/models/shap_summary.json`.
- [X] T019 [P] `code/models/train_symbolic.py` using PySR; output `data/models/symbolic_formulas.txt`; flags limitation if R² ≤ 0.0. **Dependency**: T015. **Deliverable**: `data/models/symbolic_formulas.txt`.
- [X] T072_fallback [P] Implement fallback logic in `code/models/train_symbolic.py`: If PySR returns R² ≤ 0.0, log "CONVERGENCE WARNING", default to SHAP results, and continue execution (do NOT exit with non-zero status). **Dependency**: T019. **Deliverable**: `code/models/train_symbolic.py` (updated).
- [X] T083_create_train_baselines_script [P] Create `code/models/train_baselines.py` that orchestrates training of Random Forest and Gradient Boosting (calls T017a and T017b) and logs results. **Deliverable**: `code/models/train_baselines.py`.
- [X] T020a_correct [P] Contract test for model output schema (`tests/contract/test_model_output_schema.py`). **Depends on**: `evaluate.py` logic. **Note**: Ensures paired t‑test is used. **Deliverable**: `tests/contract/test_model_output_schema.py`.
- [X] T032b [P] Updated `code/models/evaluate.py` to replace any Diebold‑Mariano test with a paired t‑test, ensuring alignment with SC‑002. **Dependency**: T020a_correct. **Deliverable**: `code/models/evaluate.py` (corrected version).
- [X] T020b [P] Re‑run `code/models/evaluate.py` (corrected) to produce `data/results/model_comparison.json`. **Dependency**: T032b. **Constraint**: Output must include `p_value`, `t_statistic`, and `r2_difference`. **Deliverable**: `data/results/model_comparison.json`.
- [X] T032b_verify [P] Unit test verifying that `model_comparison.json` contains the p-value and t-statistic required to prove the t-test was performed. **Dependency**: T020b. **Deliverable**: `tests/unit/test_model_comparison_metrics.py`.
- [X] T074_core [P] [US2] [FR-004] Implement Proxy Leakage Test in `code/models/evaluate.py`: Run ablation study removing melting point as a feature. If R² on latent heat drops by >20%, flag "PROXY LEAKAGE DETECTED" and write `data/results/leakage_report.json`. **Dependency**: T020b, T032b. **Deliverable**: `code/models/evaluate.py` (updated), `data/results/leakage_report.json`.
- [X] T074_verify [P] Contract test for `leakage_report.json` schema and content. **Dependency**: T074_core. **Deliverable**: `tests/contract/test_leakage_report_schema.py`.
- [X] T042 [P] Integration test (`tests/integration/test_training_limits.py`) that asserts each baseline model finishes ≤ 2 h and reports R² > 0.0, and that symbolic regression finishes ≤ 4 h and either produces a formula with R² > 0.0 or logs the fallback condition. **Depends on** T017a, T017b, T019, T072_fallback.
- [X] T038_limits_test [P] Test confirming that PySR respects the explicit `time_limit` and `niterations` set in `train_symbolic.py`. **Deliverable**: `tests/unit/test_symbolic_limits.py`.
- [X] T061_define_correlation_threshold (re‑used) ensures paired t‑test uses same config.

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate rules against external PCMs, perform sensitivity analysis, finalize associational framing.

- [X] T073_diag [P] [US3] Implement `code/validate/check_chemical_similarity.py` to compute Tanimoto similarity between the training set and the literature validation set. Output `data/results/chemical_similarity_report.json`. **Constraint**: This is a diagnostic report only; do NOT skip validation based on this result. **Dependency**: T013a, T023a. **Deliverable**: `code/validate/check_chemical_similarity.py`, `data/results/chemical_similarity_report.json`.
- [X] T023 (External validation) already completed above.
- [X] T023_test (integration test) already completed above.
- [X] T024 [P] Sensitivity analysis (`code/validate/sensitivity_analysis.py`) → `data/results/sensitivity_report.json`. **Depends on** T023.
- [X] T024a [P] Define acceptance threshold for robustness: false‑positive rate variation across thresholds must be ≤ 5 %. **Deliverable**: `code/validate/sensitivity_analysis.py` includes this check.
- [X] T062_define_sensitivity_threshold [P] Add `sensitivity_variation_threshold: a low sensitivity variation threshold` to `config.yaml`. **Deliverable**: updated `config.yaml`.
- [X] T062_sensitivity_threshold_test [P] Unit test verifying that the variation reported in `sensitivity_report.json` does not exceed the 5 % threshold. **Deliverable**: `tests/unit/test_sensitivity_threshold.py`.
- [X] T024a_test [P] Unit test verifying that the variation reported in `sensitivity_report.json` does not exceed the 5 % threshold. **Deliverable**: `tests/unit/test_sensitivity_threshold.py`.
- [X] T039_sweep_test [P] Test verifying fine‑grained sweep execution and that `sensitivity_report.json` contains the full list of thresholds and corresponding false‑positive/false‑negative rates. **Deliverable**: `tests/unit/test_sensitivity_sweep.py`.
- [X] T043_schema_test [P] Contract test validating `sensitivity_report.json` against `contracts/sensitivity_report.schema.yaml`. **Deliverable**: `tests/contract/test_sensitivity_report_schema.py`.
- [X] T040 [P] Extend `code/utils/collinearity_utils.py` to output detailed `data/results/collinearity_diagnostic.json` listing all flagged variable pairs and VIF scores. **Dependency**: T014. **Constraint**: Must calculate VIF > 5 and flag variables for descriptive framing. **Deliverable**: `code/utils/collinearity_utils.py`, `data/results/collinearity_diagnostic.json`.
- [X] T040_impl [P] Implement VIF calculation and flagging logic in `code/utils/collinearity_utils.py`: Compute VIF for all feature pairs, flag pairs with VIF > 5, and generate descriptive framing notes. **Dependency**: T040. **Deliverable**: `code/utils/collinearity_utils.py` (logic implemented).
- [X] T040_test [P] Unit test checking that `collinearity_diagnostic.json` contains VIF scores and flags variables with VIF > 5. **Deliverable**: `tests/unit/test_collinearity_output.py`.
- [X] T078 [P] Update `code/validate/validate_external.py` to accept `chemical_similarity_report.json` and log a warning if similarity is low, but **MUST NOT** skip the ranking test. **Dependency**: T073_diag, T075_orchestrator. **Deliverable**: `code/validate/validate_external.py` (updated).
- [X] T078_test [P] Integration test confirming that low similarity triggers a warning but does not abort validation. **Deliverable**: `tests/integration/test_similarity_warning.py`.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple user stories.

- [X] T028 [P] Update documentation:
 - `docs/architecture.md` with pipeline diagram.
 - `quickstart.md` with step‑by‑step commands and expected outputs.
 - Add `tests/integration/test_docs_updated.py` to verify sections exist. **Depends on** T026c.
- [X] T084a [P] Modify `quickstart.md` to reference the newly created `code/models/train_baselines.py` script and insert the command `python -m code.models.train_baselines`. **Deliverable**: updated `quickstart.md`.
- [X] T084b [P] Modify `plan.md` to reference the newly created `code/models/train_baselines.py` script and update the run-book section. **Deliverable**: updated `plan.md`.
- [X] T085_test_runbook_consistency [P] Integration test that checks the run‑book command in `quickstart.md` matches an existing script (`train_baselines.py`) and that documentation reflects the change. **Deliverable**: `tests/integration/test_runbook_consistency.py`.
- [X] T029 [P] Code cleanup and refactoring:
 - Run `ruff` and `isort` across `code/`.
 - Produce lint report `data/reports/lint_report.txt`.
 - CI must pass linting. **Depends on** T028.
- [X] T029_lint_test [P] CI test asserting `lint_report.txt` contains zero errors. **Deliverable**: `tests/contract/test_lint_report.py`.
- [X] T030 [P] Additional unit tests for descriptor computation and stability checks:
 - `tests/unit/test_compute_descriptors.py`
 - `tests/unit/test_stability_checks.py`
 - Require ≥ 80 % coverage. **Depends on** T012.
- [X] T031a [P] Implement config loader (`code/utils/config.py`) to read `config.yaml` and expose `max_time_seconds` and `max_memory_gb`. **Depends on** Phase 1. **Deliverable**: `code/utils/config.py`.
- [X] T031a_loader_edge_test [P] Test that malformed `config.yaml` raises a clear error. **Deliverable**: `tests/unit/test_config_loader_edge.py`.
- [X] T032a [P] Add unit test `tests/unit/test_config_loader.py` ensuring correct parsing of limits. **Depends on** T031a.
- [X] T032a_edge_cases [P] Extend config loader tests to cover invalid types and missing keys. **Deliverable**: same test file enhanced.
- [X] T031 [P] Run `quickstart.md` validation:
 - Execute `python -m code.main --config config.yaml`.
 - Verify creation of `data/results/pipeline_success.json`.
 - Include `tests/integration/test_quickstart.py`. **Depends on** T028, T031a.
- [X] T032 [P] Feasibility monitor:
 - Log total runtime and peak memory usage; assert ≤ limits in `config.yaml`.
 - Output `data/results/feasibility_report.json`. **Depends on** T031.
- [X] T032a_feasibility_test [P] Test that `feasibility_report.json` respects `max_time_seconds` and `max_memory_gb`. **Deliverable**: `tests/unit/test_feasibility_limits.py`.

---

## Phase 7: Validation & Final Polish

**Purpose**: Final validation and readiness for research review. No revision tasks here; all revisions moved to earlier phases.

- [X] T038 [P] Update PySR Execution Config in `code/models/train_symbolic.py` to explicitly set `time_limit=14400` (4 hours) and `niterations=100` (CPU‑tractable) and log budget. **Dependency**: T019. **Deliverable**: `code/models/train_symbolic.py` (updated).
- [X] T039 [P] Refine Sensitivity Analysis Sweep in `code/validate/sensitivity_analysis.py` to perform fine‑grained sweep over threshold range and output exact values in `sensitivity_report.json`. **Dependency**: T024. **Deliverable**: `code/validate/sensitivity_analysis.py` (updated).
- [X] T010_full_integration [P] Full integration test for data pipeline (`tests/integration/test_pipeline.py`). **Depends on** T015, T017a, T017b, T019, T023, T024.

---

## Phase 8: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in prior analysis regarding data integrity, test strictness, and execution order.

- [X] T070_setup (already completed) – Refactor `fetch_materials.py` to remove synthetic fallbacks.
- [X] T071 (Streaming Data Fetcher) – Implemented as part of T086 earlier.
- [X] T072_fallback (Strengthen `train_symbolic.py` convergence check) – Completed.
- [X] T073 (Chemical Similarity Check) – Completed.
- [X] T074 (Proxy Leakage Test) – Completed.
- [X] T075_orchestrator – Completed.
- [X] T076_test (Unit Test for Symbolic Regression Failure) – Completed.
- [X] T077_test (Unit Test for Strict Data Fetch) – Completed.
- [X] T078 (Integrate Similarity Check) – Completed.
- [X] T079_resolve [P] Resolve run‑book mismatch: create `code/models/train_baselines.py` that orchestrates both Random Forest and Gradient Boosting training, or update `quickstart.md` and `plan.md` to reference existing scripts. Implemented by creating the script.
- [X] T079_test [P] Verify that the run‑book command now matches an existing script (`train_baselines.py`) and that documentation reflects this change. **Deliverable**: `tests/integration/test_runbook_consistency.py`.
- [X] T086_streaming_data_fetch (already completed) – Streaming Data Fetcher.
- [X] T087_streaming_test (already completed) – Streaming Test.
- [X] T088_literature_mapping_fix [P] [US3] Implement robust mapping logic in `code/data/map_literature_pcm.py` to handle cases where literature PCMs do not have direct MP ID matches, using chemical formula and structure similarity as fallback. **Dependency**: T013a. **Deliverable**: `code/data/map_literature_pcm.py` (updated).
- [X] T089_mapping_test [P] Unit test verifying that the mapping logic correctly handles missing MP IDs and uses the fallback strategy. **Dependency**: T088. **Deliverable**: `tests/unit/test_literature_mapping.py`.
- [X] T090_final_pipeline_validation [P] End-to-end integration test that runs the full pipeline from data fetch to external validation, ensuring all components work together without errors. **Dependency**: All previous tasks. **Deliverable**: `tests/integration/test_full_pipeline.py`.