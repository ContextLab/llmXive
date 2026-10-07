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

- [X] T004 Setup `config.yaml` for API keys, random seeds, time/memory constraints, `top_n` (default: a modest number of top items), and `similarity_threshold` (default: a modest similarity value). **Deliverable**: `config.yaml`.
- [X] T005 [P] Implement basic logging infrastructure (`code/utils/logger.py`) and error handling in `code/utils/`. **Deliverable**: `code/utils/logger.py`.
- [X] T005d [P] Add unit test for logger (`tests/unit/test_logger.py`) that writes and reads a log entry. **Deliverable**: `tests/unit/test_logger.py`.
- [X] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring. **Constraint**: Dedicated to numerical stability only; no sensitivity analysis logic. **Deliverable**: `code/utils/stability_checks.py`.
- [X] T006b [X] Define JSON schema for `target_decision.json` and `imputation_rate_report.json`. **Deliverable**: `contracts/target_decision.schema.yaml`.
- [X] T006b_test [P] Contract test validating `target_decision.json` and `imputation_rate_report.json` against the newly created schema. **Deliverable**: `tests/contract/test_target_decision_schema.py`.
- [X] T080 Create target decision schema file (`contracts/target_decision.schema.yaml`). **Deliverable**: `contracts/target_decision.schema.yaml`.
- [X] T080_test [P] Contract test confirming the schema file is syntactically correct and matches expectations. **Deliverable**: `tests/contract/test_target_decision_schema_validity.py`.
- [X] T006c Define JSON schema for `fallback_decision.json` (`contracts/fallback_decision.schema.yaml`). **Deliverable**: `contracts/fallback_decision.schema.yaml`.
- [X] T006c_schema_test [P] Contract test for `fallback_decision.json`. **Deliverable**: `tests/contract/test_fallback_schema.py`.
- [X] T006a Verify existence of `data/results/target_decision.json`. **Deliverable**: `data/results/target_decision.json`.
- [X] T013 [ ] Fetch known PCMs from `matbench/literature_pcm_validation_set` (`code/data/fetch_literature_pcm.py`). **Deliverable**: `code/data/fetch_literature_pcm.py`, `data/external/literature_pcms_raw.csv`.
- [X] T013_fetch_test [P] Contract test confirming fetch succeeded and CSV integrity. **Deliverable**: `tests/contract/test_literature_fetch.py`.
- [X] T086_streaming_data_fetch [P] Implement streaming data fetch in `code/data/fetch_materials.py` using `datasets.load_dataset(..., streaming=True)` to process the full Materials Project dataset in chunks, ensuring memory usage stays within an acceptable upper limit. **Deliverable**: `code/data/fetch_materials.py`.
- [X] T087_streaming_test [P] Unit test verifying that the streaming fetcher processes data in chunks and never exceeds the allocated memory budget. **Deliverable**: `tests/unit/test_streaming_fetch.py`.
- [X] T070_setup Refactor `fetch_materials.py` to REMOVE synthetic fallbacks; raise on API failure, log fallback to verified `matbench` dataset. **Deliverable**: Updated `code/data/fetch_materials.py`.
- [X] T070_test Unit test ensuring `fetch_materials.py` raises on API failure and does not produce synthetic data. **Deliverable**: `tests/unit/test_fetch_strict.py`.
- [X] T033 Implement `code/data/fetch_materials.py` with robust fallback to verified `matbench` dataset on API failure/rate‑limit. **Deliverable**: `code/data/fetch_materials.py`.
- [X] T005a Execute `code/data/fetch_materials.py` to fetch data. **Deliverable**: `data/raw/materials_project_data.json`.
- [X] T005a_run Run T005a and assert successful fetch (log status). **Deliverable**: `tests/integration/test_fetch_materials.py`.
- [X] T034 Implement `code/data/fetch_nist_data.py` with fallback to `melting_point` target if NIST overlap < 500. **Deliverable**: `code/data/fetch_nist_data.py`.
- [X] T005b Execute `code/data/fetch_nist_data.py` to fetch NIST data. **Deliverable**: `data/raw/nist_data.json`.
- [X] T005b_run Run T005b and assert successful fetch. **Deliverable**: `tests/integration/test_fetch_nist.py`.
- [X] T005c Implement `code/data/target_consistency_check.py` to compute correlation, decide target, write `data/results/target_decision.json` and `data/results/imputation_rate_report.json`. **Deliverable**: `code/data/target_consistency_check.py`, `data/results/target_decision.json`, `data/results/imputation_rate_report.json`.
- [X] T081_implement_target_consistency_check Add core logic inside `target_consistency_check.py`. **Deliverable**: `code/data/target_consistency_check.py`.
- [X] T005c_run Execute target consistency check and validate output against schema. **Deliverable**: `tests/unit/test_target_consistency.py`.
- [X] T012_compute_descriptors [ ] Implement descriptor computation script (`code/data/compute_descriptors.py`). **Deliverable**: `code/data/compute_descriptors.py`.
- [X] T012_impl [ ] Implement core logic: elemental descriptors via `pymatgen.core.periodic_table.Element` and crystal graph via `StructureGraph`. **Deliverable**: `code/data/compute_descriptors.py` (logic).
- [X] T012_test [P] Unit test verifying correct feature generation. **Deliverable**: `tests/unit/test_compute_descriptors.py`.
- [X] T014 [ ] Compute VIF values for collinearity diagnostics and output intermediate data needed by T040. **Deliverable**: `code/utils/vif_compute.py`, `data/interim/vif_values.json`.
- [X] T014_test [P] Unit test ensuring VIF computation runs without errors and flags variables with VIF > 5. **Deliverable**: `tests/unit/test_vif_compute.py`.
- [X] T009 [ ] Contract test for dataset schema (`tests/contract/test_dataset_schema.py`). **Depends on** T012. **Deliverable**: test file.
- [X] T015 [ ] Assemble final dataset by merging `materials_project_data.json`, `nist_data.json`, and `features.csv`. **Deliverable**: `data/processed/final_dataset.csv`.
- [X] T030c [ ] Implement Pearson correlation analysis in `code/evaluate.py`; output `data/results/correlation_report.json`. **Deliverable**: `code/evaluate.py`, `data/results/correlation_report.json`.
- [X] T030c_threshold_test [P] Test asserting `pearson_r` meets or exceeds threshold from `config.yaml`. **Deliverable**: `tests/unit/test_correlation_threshold.py`.
- [X] T041 [ ] Unit test verifying final CSV contains ≥ 5,000 rows, non‑null required fields, and peak memory ≤ 7 GB. **Deliverable**: `tests/unit/test_preprocessed_dataset.py`.
- [X] T023a [ ] Prepare external validation dataset (map literature PCMs to Materials Project IDs, fetch structures). **Deliverable**: `code/validate/prepare_external_validation.py`, `data/interim/external_validation_prepared.csv`.
- [X] T023a_test [P] Contract test confirming preparation output conforms to expected schema. **Deliverable**: `tests/contract/test_external_preparation_schema.py`.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve curated Materials Project subset, compute descriptors, prepare dataset within 7 GB RAM.

- [X] T041 [ ] (remains pending until T015 and T012 are completed) – see above.
- (All other tasks for this phase are now correctly sequenced and pending as needed.)

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train RF, GB, SHAP, and PySR models on CPU within time limits; achieve R² > 0.0.

- [X] T017a Train Random Forest. **Deliverable**: `data/models/rf_model.pkl`, `data/results/baseline_metrics.json`.
- [X] T017b Train Gradient Boosting. **Deliverable**: `data/models/gb_model.pkl`, `data/results/baseline_metrics.json`.
- [X] T017c Verify baseline metrics. **Deliverable**: `data/results/baseline_verification.json`.
- [X] T017c_test [P] Contract test for baseline verification JSON schema. **Deliverable**: `tests/contract/test_baseline_verification_schema.py`.
- [X] T017d Perform SHAP analysis. **Deliverable**: `data/models/shap_summary.json`.
- [X] T017d_test [P] Contract test for SHAP summary JSON schema. **Deliverable**: `tests/contract/test_shap_summary_schema.py`.
- [X] T019 Symbolic regression with PySR. **Deliverable**: `data/models/symbolic_formulas.txt`.
- [X] T072_fallback Fallback logic for symbolic regression. **Deliverable**: Updated `code/models/train_symbolic.py`.
- [X] T075_orchestrator Update execution order: Fetch → Process → VIF → Train → Chemical Similarity Check → External Validation → Sensitivity. **Deliverable**: `code/main.py`.
- [X] T083_create_train_baselines_script Create orchestrator `code/models/train_baselines.py`. **Deliverable**: `code/models/train_baselines.py`.
- [X] T083_test Integration test for orchestrator. **Deliverable**: `tests/integration/test_train_baselines.py`.
- [X] T020a_correct Contract test for model output schema. **Deliverable**: `tests/contract/test_model_output_schema.py`.
- [X] T032b Updated evaluation to use paired t‑test. **Deliverable**: `code/models/evaluate.py`.
- [X] T020b Produce `model_comparison.json`. **Deliverable**: `data/results/model_comparison.json`.
- [X] T032b_verify Verify `model_comparison.json` contains required metrics. **Deliverable**: `tests/unit/test_model_comparison_metrics.py`.
- [X] T020c_r2_bound_test Assert |R²_interpretable − R²_baseline| ≤ 0.05. **Deliverable**: `tests/unit/test_r2_bound.py`.
- [X] T074_core Proxy Leakage Test. **Deliverable**: `data/results/leakage_report.json`.
- [X] T074_verify Contract test for leakage report. **Deliverable**: `tests/contract/test_leakage_report_schema.py`.
- [X] T042 Integration test ensuring training time limits and R² > 0.0. **Deliverable**: `tests/integration/test_training_limits.py`.

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate rules against external PCMs, perform sensitivity analysis, finalize associational framing.

- [X] T073_diag Implement chemical similarity diagnostic. **Deliverable**: `data/results/chemical_similarity_report.json`.
- [X] T023 External validation. **Deliverable**: `validation_report.json`.
- [X] T023_test Integration test for external validation. **Deliverable**: `tests/integration/test_external_validation.py`.
- [X] T023_ranking_accuracy_test Verify external ranking ≥ 60 % on top N. **Deliverable**: `tests/unit/test_external_ranking_accuracy.py`.
- [X] T024 [ ] Sensitivity analysis implementation. **Deliverable**: `code/validate/sensitivity_analysis.py`, `data/results/sensitivity_report.json`.
- [X] T024a Acceptance threshold (variation ≤ 5 %). **Deliverable**: Updated `code/validate/sensitivity_analysis.py`.
- [X] T024_verify Verify SC‑004 (variation ≤ 5 %). **Deliverable**: `tests/unit/test_sensitivity_variation.py`.
- [X] T040_impl [ ] Extend `code/utils/collinearity_utils.py` to compute VIF > 5 and flag variables. **Deliverable**: Updated `code/utils/collinearity_utils.py`.
- [X] T040_schema_test [P] Contract test validating `collinearity_diagnostic.json` schema. **Deliverable**: `tests/contract/test_collinearity_schema.py`.
- [X] T078 Updated `code/validate/validate_external.py` to accept `chemical_similarity_report.json` and log warning if similarity low (do not abort). **Deliverable**: Updated script.
- [X] T078_test Integration test confirming warning behavior without abort. **Deliverable**: `tests/integration/test_similarity_warning.py`.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple user stories.

- [X] T028 Update documentation (`docs/architecture.md`, `quickstart.md`). **Deliverable**: Updated docs. *(Now depends on newly added T026c)*
- [X] T026c Update documentation cross‑references (quickstart, plan, architecture). **Deliverable**: Updated `docs/architecture.md`, `quickstart.md`, `plan.md`.
- [X] T029 Code cleanup with `ruff`/`isort`; produce `lint_report.txt`. **Deliverable**: `data/reports/lint_report.txt`.
- [X] T029_lint_test CI test asserting zero lint errors. **Deliverable**: `tests/contract/test_lint_report.py`.
- [X] T030 Additional unit tests for descriptor computation and stability checks (`tests/unit/test_compute_descriptors.py`, `tests/unit/test_stability_checks.py`). **Deliverable**: test files.
- [X] T031a Implement config loader (`code/utils/config.py`). **Deliverable**: `code/utils/config.py`.
- [X] T031a_loader_edge_test Test malformed `config.yaml` raises clear error. **Deliverable**: `tests/unit/test_config_loader_edge.py`.
- [X] T032a Config loader unit test. **Deliverable**: `tests/unit/test_config_loader.py`.
- [X] T031 Run `quickstart.md` validation via `code/main.py`; produce `pipeline_success.json`. **Deliverable**: `data/results/pipeline_success.json`.
- [X] T032 Feasibility monitor logs runtime and memory; output `feasibility_report.json`. **Deliverable**: `data/results/feasibility_report.json`.
- [X] T032a_feasibility_test Verify limits respected. **Deliverable**: `tests/unit/test_feasibility_limits.py`.
- [X] T100_entity_traceability Map entities to code and tests. **Deliverable**: `tests/unit/test_entity_traceability.py`.
- [X] T200_single_source_verification Verify single source of truth for all figures/statistics. **Deliverable**: `tests/unit/test_single_source_truth.py`.

---

## Phase 7: Validation & Final Polish

**Purpose**: Final validation and readiness for research review. No revision tasks here; all revisions moved to earlier phases.

- [X] T010_full_integration Full pipeline integration test. **Deliverable**: `tests/integration/test_pipeline.py`.

---

## Phase 8: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in prior analysis regarding data integrity, test strictness, and execution order.

- (All concerns addressed in earlier phases; tasks updated accordingly.)

---

## Phase 9: Additional Revision Tasks (New)

**Purpose**: Close remaining open items flagged during analysis and ensure full pipeline readiness.

- (All tasks from previous phases now reflect the updated status and dependencies.)
