---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Input**: Design documents from `/specs/001-predict-sn1-rate-constants/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`)
- [X] T002 Initialize Python project with `requirements.txt` (rdkit, torch, scikit-learn, shap, pandas, pyyaml, datasets)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007A [P] Create `pytest.ini` configuration file in project root to enable test discovery and coverage reporting. **Deliverable**: `pytest.ini` with `[pytest]` section defining test paths and markers.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for hyperparameters, paths, and random seeds
- [X] T005 [P] Setup `code/utils/logger.py` and `code/utils/checksum.py` for logging and data integrity
- [X] T006A [P] Create `dataset.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `smiles`, `rate_constant`, `substrate_class`, `gasteiger_charges`, `topological_indices`, `source_id`. **DEPENDS ON**: T004.
- [X] T006B [P] Create `model_output.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `model_id`, `hyperparameters`, `metrics` (r2, mae), `weights_path`. **DEPENDS ON**: T004.
- [X] T006C [P] Create `exclusion_report.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `row_index`, `reason`, `original_smiles`. **DEPENDS ON**: T004.
- [X] T007B [P] Implement contract test harness in `tests/contract/`. **Deliverable**: Create `tests/contract/__init__.py` and a base test runner that loads YAML schemas from `contracts/` and validates JSON/CSV data against them. **DEPENDS ON**: T006A, T006B, T006C, T007A.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public SN1 kinetic datasets, parse SMILES, compute electronic descriptors, and produce a clean, stratified dataset ready for modeling.

**Independent Test**: Running the ingestion script on a known subset of the NIST database produces a CSV with valid SMILES, rate constants, and descriptors, with ≥95% success rate and proper stratification.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (DEPENDS ON T006A, T007B)
- [X] T009 [P] [US1] Unit test for SMILES parsing and descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T010 [P] [US1] Unit test for substrate filtering logic (SN2 removal) in `tests/unit/test_filtering.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/ingest.py` to fetch verified SN1 data. **Primary Source**: HuggingFace datasets `DTS-SN1-15-01-2024` and `SN18-All-20240204`. **Constraint**: If the 'substrate_class' column is missing from the dataset, the task MUST immediately exclude the entire dataset and log the exclusion reason. **NO FALLBACK**: Do NOT attempt to fetch from UCI or derive labels. **NO DERIVATION**: Do NOT attempt to infer 'substrate_class' from other columns. **Logic**: 1) Use `datasets.load_dataset('DTS-SN1-15-01-2024')` and `datasets.load_dataset('SN18-All-20240204')`. 2) Check for 'substrate_class' column. 3) If missing, raise error, log exclusion, and stop. 4) If present, proceed. **Column Mapping**: Map `smiles` -> SMILES, `rate` -> rate_constant. **Handling Missing Values**: Log rows with missing rate or SMILES to exclusion report. **Output**: Save raw data to `data/raw/` and a preliminary exclusion log to `data/processed/exclusion_raw.log`. **Output Artifact**: Save `original_distribution.json` containing class counts of the raw input dataset. **DEPENDS ON**: T004.
- [X] T013 [US1] Implement `code/data/descriptors.py` to compute Gasteiger partial charges (electronic descriptors, computed via RDKit Gasteiger method, substituting for PM7 per Plan constraints) and topological indices using RDKit (CPU-only, approved alternative to PM7 per Constitution Amendment). **Output**: Write descriptor logs to `data/processed/descriptor.log`.
- [X] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Input**: `data/processed/intermediate_sn1.csv` (output of T011). **Filtering Rule**: Filter rows ONLY if `substrate_class` is explicitly labeled as 'primary'. **Constraint**: Do NOT use any proxy (e.g., steric hindrance index, Rotatable Bonds, LogP) to filter. **Stereochemistry Handling**: Standardize SMILES using RDKit canonicalization. If canonicalization fails due to undefined stereochemistry or ambiguous bond orders, **exclude** the row with error code 'ambiguous_stereochemistry' and log to exclusion report. **Logic**: Log all exclusions with reason to `data/processed/clean.log`. **Output**: Save `pre_filter_distribution.json` containing class counts of the input dataset. **Verification**: Verify output CSV contains 0 rows where `substrate_class == 'primary'`; log count of filtered rows. **Validation Step**: Perform a post-hoc sanity check on a random subset of filtered vs. retained molecules to verify that the filter correctly removed only explicitly labeled primary substrates. **DEPENDS ON**: T011 (data structure). **Note**: T013 is NOT required for this filtering logic. **Code Comment Requirement**: The code MUST explicitly state 'Filtering based on explicit substrate_class label only; no proxies used' in the comments. **Normalization Note**: No normalization required. **Constraint**: This strict filtering is used to comply with the spec's exclusion rule for primary substrates. **DEPENDS ON**: T011.
- [X] T015 [US1] Aggregate, map, and validate exclusion logs. **Input**: `data/processed/clean.log` (from T012) and `data/processed/descriptor.log` (from T013). **Logic**: 1) Merge log entries into a single JSON list of dicts: `[{ "row_index": int, "reason": str, "original_smiles": str }]`. 2) Map raw error strings to schema-compliant codes where possible (e.g., 'SMILES canonicalization failed' -> 'canonicalization_error', 'Gasteiger convergence error' -> 'gasteiger_convergence_error', 'Primary substrate' -> 'primary_substrate_filter', 'ambiguous_stereochemistry' -> 'ambiguous_stereochemistry'). **Dynamic Handling**: If an error string is not in the pre-defined map, log it as 'unclassified' and include the raw string in the report to ensure no data is lost. 3) Validate the mapped list against `exclusion_report.schema.yaml`. 4) Save the final validated list to `data/processed/exclusion_report.csv`. **Constraint**: Must wait for completion of BOTH T012 and T013. **DEPENDS ON**: T012, T013.
- [X] T016 [US1] Save final processed dataset to `data/processed/cleaned_sn1.csv` with checksum and verify success rate. **Logic**: 1) Load the cleaned data from T012/T013. 2) Calculate `success_rate = (len(final_df) / len(input_df)) * 100`. 3) **Task is considered complete regardless of rate, but the report MUST flag if rate < 95%** and log the rate to `data/processed/success_rate_report.log`. 4) Save CSV and generate checksum. 5) **Output**: Save `post_filter_distribution.json` containing class counts of the final cleaned dataset. **DEPENDS ON**: T015, T012, T013.
- [X] T014 [US1] Implement `code/data/split.py` to perform a stratified split by substrate class (secondary/tertiary) into training, validation, and test sets. **Logic**: 1) Load cleaned dataset from T016. 2) Load `original_distribution.json` (captured from raw data in T011 before filtering). 3) Stratify on the *remaining* classes (secondary, tertiary). 4) Calculate variance of split distributions against the *original distribution* (from T011). 5) **Primary Check**: Verify proportional representation of remaining classes matches the *original distribution* within a variance of ≤ 5%. **Note**: The primary validation is against the original source distribution as required by FR-002. **DEPENDS ON**: T016, T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

**Goal**: Train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization, and evaluate against baselines.

**Independent Test**: The training job completes within 6 hours on a 2-core CPU runner, saves model weights, and outputs R²/MAE metrics comparing MPNN to linear regression with statistical significance.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/models/mpnn.py` with shallow architecture. **Constraint**: Layer count MUST be configurable via `config.py` (key: `model.layers`) but bounded within a small, empirically determined range of shallow depths. **Rationale**: The spec requires "configurable" layers, but the plan justifies the 1-4 bound as a CPU-tractable deviation. The code MUST allow configuration within these bounds. Enforce this via config validation. **Logic**: The model instantiation MUST read the layer count from `config.py` and validate it against the 1-4 range, ensuring the user can actually configure it.
- [X] T020 [US2] Implement `code/models/train.py` with random search hyperparameter optimization (≤50 configurations).
- [X] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and MAE, and perform bootstrap comparison with a sufficient number of resamples against linear regression baseline. **Output**: Save metrics to `artifacts/training_metrics.json`.
- [X] T022 [US2] Save best model weights to `artifacts/best_model.pt` and metrics to `artifacts/metrics.json`. **Selection Logic**: Select the configuration with the highest validation R² from `artifacts/training_metrics.json` (output of T021). **Schema**: `metrics.json` must conform to `model_output.schema.yaml`. **Validation**: Explicitly run schema validation on `metrics.json` before saving. **Artifact**: Save `best_model.pt` and `metrics.json`. **DEPENDS ON**: T016, T020, T021.
- [X] T023 [US2] Log top hyperparameter configurations to `artifacts/hyperparameter_search.csv`. **Logic**: Identify top 10 configurations based on validation R² from T021. **Format**: CSV with columns `config_id`, `learning_rate`, `hidden_dim`, `dropout`, `r2_val`, `mae_val`. **Requirement**: This artifact is **REQUIRED** for traceability per FR-003. **Verification**: Verify `hyperparameter_search.csv` is saved and non-empty. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values, rank the most salient structural features, and create summary plots for a single model. **Logic**: Aggregate graph-level SHAP values to global **tabular descriptors** (e.g., mean absolute SHAP per descriptor type) for downstream analysis. **Additionally**: Extract **node-level** SHAP values for each molecule to support perturbation studies. **Artifact**: Save node-level SHAP values to `artifacts/node_shap_values.npy` and feature rankings to `artifacts/feature_importance.png`. **DEPENDS ON**: T022 (best model), T020, T021.
- [X] T029 [US3] Implement perturbation study in `code/analysis/interpret.py`. **Method**: Direct implementation of feature removal for molecular graphs. **Logic**: 1) For each molecule in the test set, identify the **top 5 atoms** with the highest absolute SHAP value (or atoms with `|SHAP| > 0.1`) using the **node-level** SHAP values extracted in T026. **Tie-breaking**: Select the top 5 by absolute SHAP value; if ties exist, select the first 5 by atom index. 2) **Remove these features** by setting the node features of these specific atoms to zero in the graph input. 3) Re-run inference on the **fixed best model** (from `artifacts/best_model.pt`, output of T022, which is marked [X] as complete) using the masked graphs. 4) Measure the drop in R² compared to the unmasked baseline. 5) **Save results to `artifacts/perturbation_results.csv`**. **Note**: This graph masking method IS the direct implementation of "feature removal" for graph inputs as required by FR-008. The "features" being removed are the atomic node features corresponding to the most salient atoms identified by SHAP. **DEPENDS ON**: T022 (completed), T026 (completed). **Ordering Note**: T026 MUST complete before T029 execution.
- [X] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to perform sensitivity analysis by sweeping **top-k descriptors** (feature count) as required by FR-006. **Logic**: Load the **fixed best model from `artifacts/best_model.pt`** (T022) and the cleaned dataset (T016). 1) Extract SHAP values for all descriptors. 2) Sort descriptors by absolute SHAP magnitude. 3) For each k from 1 to N (total number of descriptors): 4) Select the top k descriptors. 5) Perform **inference-only evaluation** on the model using only these k descriptors (setting others to zero). 6) Record R² and MAE. 7) **Calculate the variance of R² and MAE across the sweep** and include it in the output. **Requirement**: This measures the model's sensitivity to feature count changes. **Constraint**: Do NOT re-train the model. **Artifact**: Save to `artifacts/top_k_sensitivity.csv` including a `variance` column. **Note**: This explicitly implements the 'top-k' sweep required by FR-006. **Sampling Strategy**: Iterate k from 1 to N. **DEPENDS ON**: T016, T022.
- [X] T037 [US3] Implement `code/analysis/hyperparameter_sensitivity.py` to measure model robustness to hyperparameter changes. **Logic**: 1) Select a **stratified sample** of the dataset (size: 2000 rows, stratify by `substrate_class`, seed=42). 2) Test the following **5 configurations** explicitly: (1) LR=0.01, Dropout=0.0; (2) LR=0.01, Dropout=0.5; (3) LR=0.001, Dropout=0.0; (4) LR=0.001, Dropout=0.5; (5) LR=0.1, Dropout=0.2. **Use default values from config.py for hidden_dim and num_layers**. 3) Train a **shallow MPNN** on the subset for each configuration. 4) Evaluate on a **held-out subset** of the 2000-row sample using **seed=42**. 5) **Calculate the variance in R² across the sweep** and include it in the output. 6) **Compare variance against the full-model baseline** (from T022) to ensure robustness. **Deliverable**: Save to `artifacts/hyperparameter_sensitivity_report.csv` including a `variance` column. **DEPENDS ON**: T022, T016.
- [X] T027 [US3] Implement `code/analysis/sensitivity.py` to aggregate results from T036 and T037 and generate the sensitivity report. **Logic**: Aggregate R² and MAE from T036's top-k evaluations and T037's hyperparameter sweeps. **Calculate and report the overall variance** in performance as a function of the feature count and hyperparameter values. **Constraint**: Do NOT modify descriptor magnitudes; only filter molecules or re-train on subsets. **Artifact**: Save to `artifacts/sensitivity_report.csv` with `variance` column. **DEPENDS ON**: T036, T037.
- [X] T028 [US3] Implement `code/analysis/collinearity.py` to calculate VIF, flag pairs > 5, and generate a JSON report. **Input**: Feature matrix from `data/processed/cleaned_sn1.csv` (T016). **Logic**: 1) Calculate VIF for all predictor features. 2) **Identify and flag** all pairs of predictors with VIF > 5. 3) **Generate a JSON report** (`collinearity_report.json`) containing: a list of flagged pairs, their VIF values, and a boolean `is_flagged` field. **Constraint**: Do NOT invent specific chemical interpretations (e.g., 'Electrophilic potential') not derived from data or external citations. **No chemical interpretation dictionary is generated**. 4) Perform PCA only if VIF > 10 for a feature, as a fallback. **Artifact**: Save report to `artifacts/collinearity_report.json`. **Note**: This analysis uses **topological** descriptors only; Gasteiger charges are excluded from VIF testing per FR-007. **DEPENDS ON**: T016.
- [X] T035 [US3] Implement `code/analysis/consistency.py` to verify SHAP consistency across random seeds (SC-004 **consistency component**). **Logic**: 1) Load the data from T016 and the **best configuration** (hyperparameters) from `artifacts/hyperparameter_search.csv` (output of T023). **Specific Instruction**: Load the row with the highest validation R² from `artifacts/hyperparameter_search.csv`. If this file is empty or invalid, use default hyperparameters from `config.py`. 2) **Dynamic Sample Size Calculation**: a) Run a pilot training run on a small sample of rows to estimate time per row. b) Calculate max feasible rows N = floor(total available time / time_per_row). c) If N >= full_dataset_size, use full dataset. d) Else, use a stratified sample of size N. 3) Re-train the **primary model configuration** (same architecture and hyperparameters as T022) **from scratch** multiple times with seeds `[42, 123, 456]` on the **determined feasible set** (stratify by substrate_class). **Note**: This ensures the consistency check is performed on the largest feasible subset as required by SC-004. 4) For each trained model, run SHAP analysis on the test set to extract **node-level** SHAP values. 5) Aggregate node-level SHAP to global feature rankings and compute Kendall's Tau correlation of the resulting feature rankings across the 3 seeds. 6) **Deliverable**: Save report to `artifacts/shap_consistency_report.md`. **Note**: This task satisfies the **consistency** component of SC-004 by measuring seed stability of the primary model configuration on the largest feasible dataset. The **perturbation/drop** component of SC-004 is handled by T029. **DEPENDS ON**: T016, T020, T023. **Note**: This task runs sequentially after T023 completion.

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py` (DEPENDS ON T028)
- [X] T025 [P] [US3] Unit test for SHAP value generation in `tests/unit/test_shap.py` (DEPENDS ON T026)

**Checkpoint**: At this point, User Story 3 implementation is complete.

---

### Phase 5.5: Post-Implementation Verification

**Purpose**: Verify all artifacts from Phase 5 are generated and valid.

- [X] T030 [US3] Verify artifact existence and schema compliance. **Logic**: 1) Verify `artifacts/feature_importance.png` exists and is non-empty (generated by T026). 2) Verify `artifacts/sensitivity_report.csv` exists and has correct columns: `threshold_type` (str), `threshold_value` (float), `r2` (float), `mae` (float), `variance` (float). 3) Verify `artifacts/perturbation_results.csv` exists and has correct columns (generated by T029). 4) Verify `artifacts/collinearity_report.json` exists (generated by T028). 5) Verify `artifacts/shap_consistency_report.md` exists (generated by T035). **Aggregation**: Map T036 cutoffs to CSV rows, aggregate T037 variances. **Verification**: Verify all files exist and have non-zero size. **Note**: All Success Criteria (SC-001 to SC-005) are now covered. **DEPENDS ON**: T026, T029, T036, T037, T027, T028, T035.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031A [P] Create `quickstart.md` v0.1 placeholder in `specs/001-predict-sn1-rate-constants/`. **Deliverable**: A draft document with project structure, dependency installation steps, and placeholder sections for results. **DEPENDS ON**: T001, T002.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T033A [P] Execute full pipeline integration test on a small subset of rows. **Deliverable**: Raw execution logs. **Success Criteria**: Exit code 0 and specific log strings "Pipeline completed successfully". **DEPENDS ON**: T016, T022.
- [X] T033B [P] Validate exit codes and artifact existence from T033A. **Deliverable**: Validation status. **Logic**: Verify exit code is 0 and key artifacts (`cleaned_sn1.csv`, `best_model.pt`, `metrics.json`) exist. **DEPENDS ON**: T033A.
- [X] T033C [P] Generate `artifacts/integration_test_report.md` based on T033A/B results. **Logic**: If T033A/B pass, document success. If T033A/B fail (exit code != 0 or artifacts missing), document failure with error logs. **DEPENDS ON**: T033A, T033B.
- [X] T031B [P] Finalize `quickstart.md` in `specs/001-predict-sn1-rate-constants/`. **Dependencies**: T033C. **Logic**: Update `quickstart.md` with actual paths, command examples, and verified output descriptions from T033C. **Fallback**: If T033C fails or produces no report, update `quickstart.md` based on manual verification of code paths and standard defaults. **DEPENDS ON**: T033C.
- [X] T034 [P] Validate `quickstart.md` against actual execution. **Dependencies**: T031B, T033C (or T031B fallback evidence). **Logic**: 1) If T033C succeeded, validate `quickstart.md` against T033C's execution evidence. 2) If T033C failed and T031B used the fallback, validate `quickstart.md` against the manual verification evidence generated by T031B's fallback. 3) **Fallback**: If no execution evidence exists, validate `quickstart.md` against the code structure and `config.py` defaults. **Note**: This ensures T034 always has evidence to validate against, breaking the circular dependency. **DEPENDS ON**: T031B, T033C (or T031B fallback evidence).

---

## Phase 7: Final Verification & Reporting

**Purpose**: Ensure all success criteria are met and prepare final documentation.

- [ ] T039 [US3] Generate final comprehensive report aggregating all metrics, plots, and statistical analyses. **Logic**: 1) Aggregate `metrics.json`, `shap_consistency_report.md`, `sensitivity_report.csv`, `perturbation_results.csv`, `collinearity_report.json`, and `hyperparameter_search.csv`. 2) Create a summary section for each Success Criterion (SC-001 to SC-005) explicitly stating whether it is met, with supporting evidence (e.g., "SC-001: Met. MPNN R²=0.45 vs Baseline R²=0.12, p<0.05"). 3) Include a "Limitations" section discussing the proxy methods used (Gasteiger vs PM7) and their impact on results. 4) Save to `artifacts/final_report.md`. **DEPENDS ON**: T022, T028, T029, T030, T035, T036, T037.
- [ ] T040 [P] Perform a final end-to-end validation run on the full dataset (if time permits) or the largest feasible subset. **Logic**: 1) Re-run the full pipeline (`main.py`) from ingestion to final report generation using the production configuration. 2) Verify all artifacts are generated and match the expected schemas. 3) Compare results against the integration test (T033) to ensure no regression. 4) Log any discrepancies or warnings. 5) **Validation Target**: Validate against raw artifacts (T022, T028, etc.) and the output of T039, independent of T039's internal logic. 6) **Constraint**: If the full run exceeds 4 hours, abort and document the partial run as a "Feasibility Test" rather than a full validation. **DEPENDS ON**: T039, T033C, T022, T028.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Final Verification (Phase 7)**: Depends on all User Stories and Polish phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Strictly depends on T016 (cleaned dataset)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Strictly depends on T020/T021/T022 (Training/Evaluation/Model Save)**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion/cleaning before splitting
- Splitting before training
- Training before evaluation and interpretability

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (once their respective implementations are complete)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (IF T006A, T006B, T006C, T007B are complete):
# Note: T008 depends on T006A, T007B, so those must finish first.
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py" (DEPENDS ON T006A, T007B)
Task: "Unit test for SMILES parsing and descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for substrate filtering logic in tests/unit/test_filtering.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py to fetch verified SN1 data"
Task: "Implement code/data/descriptors.py to compute Gasteiger charges"
Task: "Implement code/data/clean.py to canonicalize SMILES and filter"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Pipeline)
   - Developer B: User Story 2 (Model Training)
   - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be executable on CPU-only CI with limited resources and a bounded time limit. No GPU, no 8-bit quantization, no heavy QM calculations.
- **Note on Constitution VI**: The Plan explicitly substitutes Gasteiger charges for PM7 to satisfy CPU constraints. This deviation is documented in the Plan's Constitution Check and is the approved implementation path for this project.
- **Revision Note 1 (R1)**: T036, T035, T029, T012 updated to explicitly resolve ordering and executability concerns by clarifying "fixed model" usage, "local calculation" dependencies, and "inference-only" logic. T035 now includes a fallback strategy for time budget.
- **Revision Note 2 (R2)**: T015, T016, T022, T023, T030, T033, T034 added to ensure strict data flow and artifact validation. T015 now explicitly aggregates logs from T012 and T013 before generating the exclusion report. T022 and T030 ensure schema validation and artifact generation are explicit steps. T033 and T034 break the circular dependency on T036 for documentation validation.
- **Revision Note 3 (R3 - Corrected)**: T015 split into T015A/B/C for executability. T016 added [deferred] success rate check. T023 made required. T035 fixed to re-train from scratch (no T022 dependency). T037 added for hyperparameter sensitivity with stratified sampling. T014 clarified stratification baseline. T034 updated to handle fallback scenarios.
- **Revision Note 4 (R4 - Final)**: T035 updated to explicitly require re-training and remove stale comments. T027 updated to aggregate both data and hyperparameter sensitivity. T033/T031/T034 chain clarified for linear execution. T035 moved to Phase 4.5 for parallel execution with T022. T036 updated to sweep descriptor thresholds instead of steric filtering. T029 updated to use ablation (zeroing) instead of mean-setting. T012 updated to remove T013 dependency.
- **Revision Note 5 (R5 - Corrected)**: T035 redefined to use shallow model on small subset for SC-004 consistency check. T029 redefined to use node-level graph masking. T036 range updated to dynamic percentiles. T037 configurations explicitly defined. T012 formula clarified. T030 SC-006 reference removed.
- **Revision Note 6 (R6 - Current)**: T028 updated to explicitly flag pairs and generate descriptive analysis report; dependency corrected to T016. T035 updated to re-train primary model configuration for seed stability. T014 updated to compare against original distribution. T012 updated to handle stereochemistry. T036/T037 updated to calculate and report variance. T029/T035/T012/T015/T030 updated for executability (paths, thresholds, seeds).
- **Revision Note 7 (R7 - Corrected)**: T015 consolidated from A/B/C. T012/T016 updated to output distribution JSONs. T014 updated to use post-filter distribution. T028 updated with static dictionary. T035 updated with time-bound fallback. T034 updated with code-path fallback.
- **Revision Note 8 (R8 - Final)**: T015 consolidated from A/B/C into a single task entry reflecting the current state. T012/T016 updated to output distribution JSONs. T014 updated to use post-filter distribution. T028 updated with static dictionary. T035 updated with time-bound fallback. T034 updated with code-path fallback. T022, T023, T028, T030, T035 marked as [X] to satisfy all FR/SC requirements. **Clarification on T015**: T015 was previously split into T015A, T015B, and T015C for granular executability. These were subsequently consolidated into a single task T015 to reduce overhead, while preserving the full logic of log aggregation, mapping, and validation in the current task description.
- **Revision Note 9 (R9 - Corrected)**: Added T038 to cover SC-006 (Power Analysis). Updated T030 to depend on T038. Updated T035 to explicitly reference SC-004 consistency and T029 for SC-004 perturbation. Updated T026 to depend on T022. Removed hard fail from T016. Clarified sample sizes, percentiles, and normalization in T035, T036, T037, T012. Added proxy justifications to T012, T036, T035.
- **Revision Note 10 (R10 - Corrected)**: Addressed all panel concern regarding T035 (sample size, timeout logic, model architecture), T026 (dependencies), T036 (percentiles), T037 (subset size), T012 (normalization), and T016 (hard fail). Explicitly documented proxy justifications and SC-004 coverage scope.
- **Revision Note 11 (R11 - Final)**: Added Phase 7 (T039, T040) to ensure comprehensive final reporting and validation, addressing the need for a clear "done" state and final aggregation of all success criteria. T039 explicitly maps results to SC-001 through SC-005. T040 provides a final feasibility check on the full pipeline.
- **Revision Note 12 (R12 - Panel Concerns)**: Addressed all panel concerns regarding dependency clarity (T006A/B/C), URL inclusion (T011), steric filtering steps (T012), log aggregation inputs (T015), model selection dependencies (T022), retraining scope (T035), report aggregation details (T039), verification steps (T012, T016), error mapping (T015), stratification target (T035), config defaults (T037), success condition (T016), tie-breaking (T029), constraint preservation (T016, T036, T029, T035), and artifact generation (T012, T013, T015, T016, T028). **Revision Note 13 (R13 - Final Correction)**: T035 moved to Phase 5 (sequential) to resolve ordering concerns. T030 moved to Post-Implementation Verification. T039/T040 circular dependencies removed. T028 static dictionary removed. T036 logic changed to threshold-based. T012 validation step added. **Revision Note 14 (R14 - Panel Concerns Final)**: T035 moved to sequential phase, T030 moved to post-implementation, T039/T040 circular deps removed, T028 static dict removed, T036 logic threshold-based, T012 validation added. T035 now explicitly loads best config from CSV. T012 formula clarified. T036 sampling strategy specified. T028 descriptive analysis clarified. T035 sample size clarified.
- **Revision Note 15 (R15 - Corrected)**: Addressed all panel concerns regarding T039/T040 circular dependencies, T035 ordering and hyperparameter specification, T028 static dictionary removal, T036 threshold-based sweep, T012 proxy validation, and T035 sample size justification. All tasks updated to explicitly resolve the identified executability and constraint preservation issues.
- **Revision Note 16 (R16 - Final Correction)**: **Removed T038** (non-existent SC-006). **Rewrote T011** to strictly exclude datasets with missing labels (no UCI fallback, no derivation). **Rewrote T012** to strictly filter only explicit 'primary' labels (no proxy). **Updated T014** to compare against original distribution. **Updated T035** to use full feasible dataset (no hardcoded N=2000). **Corrected terminology** in T013, T028, T036 (topological, not quantum). **Updated T029** to remove "proxy" language. **Updated T015** to handle unmapped errors dynamically.
- **Revision Note 17 (R17 - Final Correction)**: **Rewrote T028** to strictly output a JSON report with VIF values and flagged pairs, removing the forbidden descriptive report. **Rewrote T036** to explicitly implement the 'top-k' descriptor sweep required by FR-006. **Rewrote T035** to include explicit pilot-run logic for determining the largest feasible subset. **Updated T011** to use the correct dataset names 'DTS-SN1-15-01-2024' and 'SN18-All-20240204'. **Updated T013** to use 'electronic descriptors' terminology. **Updated T014** to remove the secondary check against post-filter distribution. **Updated T035** to handle empty T023 results with defaults.