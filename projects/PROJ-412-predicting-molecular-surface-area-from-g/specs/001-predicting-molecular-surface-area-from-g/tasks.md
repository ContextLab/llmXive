# Tasks: Predicting Molecular Surface Area from Graph Convolutional Networks

**Input**: Design documents from `/specs/001-predicting-molecular-surface-area/`
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

**Purpose**: Project initialization, directory structure, and schema generation.

- [ ] T001a [P] Create `code/`, `data/`, `tests/`, `results/`, and `logs/` directory structures. Specifically: `code/`, `code/data/`, `code/models/`, `code/eval/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/splits/`, `data/schemas/`, `tests/contract/`, `tests/unit/`, `tests/integration/`, `results/reports/`, `results/plots/`, `results/baseline/`, `results/predictions/`, and `logs/`.
- [ ] T001b [P] Create `data/` directory structure: `data/raw/`, `data/processed/`, `data/splits/`, `data/schemas/`. (Note: T001a covers this, but kept for clarity if split later).
- [ ] T001c [P] Create `tests/` directory structure: `tests/contract/`, `tests/unit/`, `tests/integration/`.
- [ ] T001d [P] Create `results/` directory structure: `results/reports/`, `results/plots/`, `results/baseline/`, `results/predictions/`.
- [X] T002 [P] Create `code/requirements.txt` containing pinned versions of: `rdkit`, `pandas`, `scikit-learn`, `pyyaml`, `numpy`, `pytest`, `ruff`, `black`, `datasets`, `huggingface_hub`. Install torch and torch-geometric using: `pip install torch --index-url https://download.pytorch.org/whl/cpu` and `pip install torch-geometric --index-url https://download.pytorch.org/whl/cpu`. Do not use `torch (cpu)` as a package name.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by generating `pyproject.toml` and `.ruff.toml` configuration files with project-specific rules.
- [X] T004 [P] Generate `data/schemas/static_schema.yaml` defining the expected fields for the processed dataset (SMILES, node_features, edge_features, surface_area, molecular_weight).
- [X] T005 [P] Generate `data/schemas/model_schema.yaml` defining the expected fields for model output (model_type, metrics, hyperparameters).
- [X] T006 [P] Generate `data/schemas/sensitivity_schema.yaml` defining the expected fields for sensitivity reports (thresholds, success_rates, corrected_p_values).
- [ ] T049 [P] Implement pre-flight network connectivity check in `code/utils/network_check.py`. This task must run before any ingestion tasks to verify access to ZINC15.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/__init__.py` and environment configuration loader
- [X] T008a [P] Setup logging infrastructure in `code/utils/logging.py`
- [ ] T009 [P] Create base data models (Molecule, Graph, EvaluationResult) in `code/models/`
- [X] T010 [P] Implement seed pinning utility for reproducibility in `code/utils/seed.py`
- [X] T011 [P] Setup dataset checksumming utility in `code/utils/checksum.py`
- [ ] T017 [P] Implement SMILES validation utility in `code/utils/validators.py`. This utility MUST validate SMILES syntax and return a list of invalid strings. It must be used by T048 and T014. **Output**: `code/utils/validators.py` containing `validate_smiles(smiles_list)` function.
- [ ] T018 [P] Implement logging infrastructure for excluded molecules and dataset statistics in `code/utils/logging.py` (extending T008a). This utility MUST handle JSON logging for excluded molecules to `logs/excluded_molecules.log` and `logs/ingestion_errors.log`. **Output**: `code/utils/logging.py` with `log_excluded_molecules(count, smiles_list)` and `log_errors(errors)` functions.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest SMILES, convert to 2D graphs, generate 3D SASA labels, and split data.

**Independent Test**: A researcher can run the data pipeline script and verify that a CSV/Parquet file is produced containing SMILES, node/edge feature matrices, and a numeric surface area column, with no missing values in the target column for the training set.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py` validating against `data/schemas/static_schema.yaml` (generated by T004) to ensure input format compliance before processing.
- [X] T013 [P] [US1] Integration test for SMILES ingestion pipeline in `tests/integration/test_ingest.py` (must run after T048)

### Implementation for User Story 1

- [ ] T048 [US1] Implement SMILES ingestion from ZINC15 using `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM. Fetch and process molecules in fixed-size chunks. **Strict Source Logic**: Check `DATA_SOURCE_OVERRIDE` environment variable. If present, use that source exclusively. If absent, fetch ONLY from ZINC15. Raise a critical error if the source is invalid or inaccessible. **Add Max Atoms Filter**: Implement a filter to exclude molecules with >100 atoms to prevent memory overflow, logging the count of excluded molecules to `logs/excluded_molecules.log` in JSON format using T018. **Invalid SMILES Handling**: Use T017 to catch syntax errors during parsing and log the specific invalid SMILES strings to `logs/ingestion_errors.log`. Validate syntax. **Schema Validation**: Validate against `data/schemas/static_schema.yaml` AND verify that the dataset contains the necessary fields or metadata to support 3D conformer generation (e.g., valid valence, atom types) to ensure downstream T015 will succeed. **Chunk Integrity**: After processing each chunk, verify that the number of rows in the output parquet matches the number of valid molecules in the input chunk (minus excluded ones). If the count is inconsistent, raise an error. The output will be written to `data/raw/chunk_*.parquet`. **Dependency**: T017, T018, T008a.
- [ ] T014 [US1] Implement 2D graph feature extraction (atom type, hybridization, charge) using RDKit in `code/data/preprocess.py`, and **calculate Molecular Weight** for each molecule. **Apply Max Atoms Filter**: Explicitly implement a filter to exclude molecules with >100 atoms BEFORE outputting the file, logging the count of excluded molecules to `logs/excluded_molecules.log` using T018. **Merge T014b**: This task now includes the Molecular Weight calculation previously in T014b. Output `data/processed/graphs_with_features.parquet` containing SMILES, node_features, edge_features, and `molecular_weight`. **Note**: This task must run after T048. **Dependency**: T048, T018.
- [ ] T015 [US1] Implement 3D conformer generation (lowest energy) and SASA calculation in `code/data/preprocess.py` with chunked processing. **Invoke the utility logic** (previously T008b) to log the RDKit parameters used for conformer generation into `data/processed/conformer_params.json`. **Generate `data/processed/failure_report.csv`** with columns `[smiles, failure_reason, atom_count]` for any failed conformers BEFORE halting. **Schema**: `failure_reason` must be a string enum (e.g., 'ETKDG_FAIL', 'MINIMIZATION_FAIL', 'INVALID_VALENCE'). **Halt Logic**: If the failure rate exceeds 10%, generate `data/processed/failure_report.csv` and THEN halt with a critical error. Log failure counts to `logs/conformer_failures.log`. **Merge SASA**: Explicitly merge the calculated SASA values into the final training artifact `data/processed/paired_dataset.parquet` (extending T014's output) to create a column `surface_area` (float, Å²). **Verification**: Ensure `data/processed/conformer_params.json` exists and contains keys `numThreads`, `maxAttempts`, `energyMinimizationSteps`. Ensure `data/processed/paired_dataset.parquet` contains the `surface_area` column with no NaN values. **Dependency**: Must run after T014 (which produces the input file with MW and features). **Atomicity**: The generation of `failure_report.csv` MUST be atomic and complete before the halt error is raised.
- [ ] T016 [US1] Implement data splitting logic (stratified by Molecular Weight) generating `data/splits/train_indices.csv`, `data/splits/test_indices.csv`, and `data/splits/split_report.json`. **Dependency**: Must run after T014 (to ensure MW values are available) and T015 (to ensure SASA values are available for the full dataset before splitting). **Execute the Kolmogorov-Smirnov (KS) test** comparing the `molecular_weight` column of the training set vs the test set. **Verification**: Output `data/splits/split_report.json` containing the key `ks_p_value` with a value > 0.05. **Failure Handling**: If p <= 0.05, generate `data/splits/split_error_report.json` with details and raise an error. Ensure `train_indices.csv`, `test_indices.csv`, and `split_report.json` (or `split_error_report.json`) are all created.
- [ ] T051 [US1] **REMOVED**: Pilot check for conformer stability was removed as scope creep. The Spec Edge Cases only mandate halting if the failure rate exceeds 10%, which is handled by T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GCN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight CPU-tractable GCN and a Baseline on 2D descriptors, then compare performance.

**Independent Test**: The training script runs to completion within the CI limit, producing two model artifacts and a results report showing MAE, RMSE, R² for both, along with a statistical significance test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py` validating against `data/schemas/model_schema.yaml` (generated by T005)
- [X] T020 [P] [US2] Integration test for training loop and early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T021a [US2] Implement lightweight GCN model definition (PyTorch Geometric, CPU-only) in `code/models/gcn.py` containing class `GCNModel` with `forward(input_tensor)` method
- [ ] T021b [US2] **Train Linear Regression Baseline**: Train a Linear Regression model on molecular descriptors (MW, atom count, etc.) using `code/models/baseline.py`. This serves as a practical baseline to compare against the GCN, satisfying Spec FR-004's requirement to "train a Geometry-Based Baseline" (interpreted as a model trained on geometric descriptors). **Output**: `results/baseline/baseline_model.pkl` and `results/predictions/baseline_predictions.parquet` containing columns `[smiles, predicted_sasa, error]`. **Dependency**: Must run after T016 (split indices).
- [ ] T021c [US2] **Train Geometry-Based Baseline**: Train a model that uses 3D geometric features (e.g., surface area components, shape descriptors derived from conformers) to predict surface area. This task explicitly implements the "Geometry-Based Baseline" required by FR-004 and FR-005. **Action**: Generate 3D conformers for the training set (if not already done) and extract geometric features. Train a model (e.g., MLP or Linear Regression on geometric features) to predict SASA. **Output**: `results/baseline/geometry_baseline_model.pkl` and `results/predictions/geometry_baseline_predictions.parquet`. **Dependency**: Must run after T016 (split indices) and T015 (3D generation).
- [ ] T024 [US2] **Geometry Oracle Evaluation (Theoretical Limit)**: Compute SASA for the test set using RDKit directly (Ground Truth) without training a model. This serves as the theoretical performance limit (the "Geometry Oracle") as defined in Plan.md and Constitution Principle VI. **Action**: Load test set molecules from `data/splits/test_indices.csv`. Generate 3D conformers and calculate SASA directly using RDKit. **Output**: `results/baseline/oracle_sasa.parquet` with columns `[smiles, calculated_sasa]`. **Note**: This is a theoretical limit reference, NOT the primary baseline for statistical comparison. **Dependency**: Must run after T016 (split indices) and T015 (processed dataset with 3D conformers).
- [ ] T022 [US2] Implement training loop with early stopping (patience=5, max 50 epochs) in `code/models/train.py`, incorporating gradient accumulation logic (merged from T050). **Output**: `results/predictions/gcn_predictions.parquet` containing columns `[smiles, predicted_sasa, error]`. **Verification**: Ensure `results/predictions/gcn_predictions.parquet` exists with the specified columns. **Dependency**: Must run after T021a and T016.
- [ ] T023 [US2] Implement evaluation metrics (MAE, RMSE, R²) in `code/eval/metrics.py`
- [ ] T040 [US2] **Calculate Model Performance Metrics**: Compute aggregate metrics (MAE, RMSE, R²) for the GCN model (from T022), the Linear Regression Baseline (from T021b), the Geometry-Based Baseline (from T021c), and the Geometry Oracle (from T024) on the test set. **Output**: `results/reports/model_metrics.json` containing keys `gcn_mae`, `baseline_mae`, `geometry_baseline_mae`, `oracle_mae`, `gcn_r2`, `baseline_r2`, `geometry_baseline_r2`, `oracle_r2`. **Verification**: Ensure the JSON file exists and contains the specified keys. **Dependency**: Must run after T022, T021b, T021c, and T024.
- [ ] T025 [US2] Integrate training and evaluation to produce final comparison report generating `results/reports/model_comparison.json`. **Verification**: Ensure the JSON file exists and contains keys `gcn_mae`, `geometry_baseline_mae`, `gcn_r2`, `geometry_baseline_r2`, `p_value`, and `cohen_d`. Explicitly calculate and report the raw MAE, RMSE, and R² for the GCN and the **Geometry-Based Baseline (T021c)**. Perform a **paired t-test** comparing the prediction errors of the GCN model and the **Geometry-Based Baseline (T021c)**. **Note**: This comparison satisfies Spec FR-005 and US-2 by comparing two predictive models. The Geometry Oracle (T024) is included for theoretical context only and is NOT used in the paired t-test. **Dependency**: Must run after T022, T021c, and T040. (T024 is optional context).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on MAE thresholds (absolute only) and apply multiple-comparison corrections.

**Independent Test**: The analysis script re-runs the evaluation with modified thresholds and generates a report showing how success rates change, including corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_report.py` validating against `data/schemas/sensitivity_schema.yaml` (generated by T006)
- [ ] T027 [P] [US3] Unit test for Bonferroni/FDR correction logic in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T028a [P] [US3] Define threshold configuration in `code/config.py`. Set `SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.1]` (float, Å²) as mandated by FR-006.
- [ ] T028 [US3] Implement sensitivity analysis script sweeping **absolute** MAE thresholds {0.01, 0.05, 0.1} Å² (as mandated by FR-006) in `code/eval/sensitivity.py`. **Dependency**: Must run after T022 (GCN Predictions) and T021c (Geometry-Based Baseline Predictions). **Action**: Load per-molecule predictions from `results/predictions/gcn_predictions.parquet` and `results/predictions/geometry_baseline_predictions.parquet`. Calculate success rates for each threshold. **Output**: `data/processed/sensitivity_absolute.csv` with columns `[threshold, success_rate, sample_size]`. **Format**: `threshold` (float), `success_rate` (float, 0.0-1.0), `sample_size` (int). **Primary Verification**: This is the mandatory verification path per Spec FR-006. The report must explicitly state that this is the primary metric and justify the threshold choice against experimental error. **Verification**: Verify that the sum of success_rate across thresholds is not used for aggregation, but each is reported independently. **Note**: The Plan.md FR/SC Coverage Map and this Task are aligned to use Spec-compliant thresholds {0.01, 0.05, 0.1} Å². **Dependency**: T028a. **Clarification**: This task implements ONLY the absolute thresholds {0.01, 0.05, 0.1} Å². No relative threshold sweep is implemented or referenced.
- [ ] T029 [US3] Implement multiple-comparison correction (Bonferroni or FDR) for threshold sweep results in `code/eval/sensitivity.py`. **Condition**: Apply correction **whenever** multiple tests (n > 1) are performed, as mandated by Spec FR-007. **Method Selection**: If `n <= 5`, use Bonferroni correction; if `n > 5`, use False Discovery Rate (FDR) correction. Specify the chosen method and the condition in the output report.
- [ ] T030 [US3] Generate sensitivity report with threshold justification and adjusted p-values writing `results/reports/sensitivity_analysis.md`. **Dependency**: Must run after T028 (Absolute), T029 (Correction), and T040 (Model Metrics). **Note**: Relative threshold sweep removed per Spec FR-006. **Justification Requirement**: The report must explicitly state the justification for the primary threshold by citing a specific literature source or standard for experimental error margins in surface area measurement, moving from an unverified assertion to a research-backed conclusion. **Source**: Cite from `research.md` or `spec.md`.
- [ ] T031 [US3] Create visualization plots for sensitivity curves in `results/plots/`. **Verification**: Output `.png` files named `sensitivity_absolute.png` showing x-axis: threshold, y-axis: success_rate.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Schema Generation & Polish

**Purpose**: Generate missing schema files and perform final polish.

- [ ] T032a [P] Update `README.md` with project overview, installation instructions, and usage examples.
- [ ] T032b [P] Update `docs/` with detailed API documentation for key modules (`code/data/`, `code/models/`, `code/eval/`).
- [ ] T033 Code cleanup and refactoring of data processing scripts
- [ ] T034a [P] Refactor `code/data/preprocess.py` to implement chunked processing.
- [ ] T034b-PilotExec [P] Implement pilot runtime measurement. **Action**: Execute a pilot check on a fixed subset of 100 molecules (seed=42) to measure actual time per molecule for 2D feature extraction and 3D conformer generation. Output `results/reports/pilot_timing.json` with the measured time per molecule.
- [ ] T034b-Report [P] Analyze pilot runtime and determine feasible sample size. **Action**: Use the **empirical** measured value from T034b-PilotExec to determine the feasible sample size for the full dataset within the Plan's time budget. Calculate feasible sample size as `floor(TIME_BUDGET / measured_time_per_molecule)`, where `TIME_BUDGET` is read from `code/config.py` (default '[deferred]' or CI profile). Generate `results/reports/pilot_timing.md` documenting the pilot size, the measured time per molecule, and the resulting feasible sample size. **Constraint**: Explicitly state that the time budget is a plan-level estimate subject to the final CI runner profile.
- [ ] T035 [P] Additional unit tests for edge cases (invalid SMILES, memory overflow) in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation
- [ ] T052-Run [P] Execute the pipeline. **Decision Logic**: Execute the pipeline on the representative subset used in T034b-PilotExec. Measure the actual runtime. Output `results/reports/pipeline_execution.log`.
- [ ] T052-Verify [P] Verify pipeline runtime against the Plan's goal. **Action**: Compare the measured time from T052-Run against the Plan's time budget (read from `code/config.py`) and the Spec's '[deferred]' limit. Generate `results/reports/final_runtime_verification.md`. **Constraint**: Explicitly state that the time budget is a plan-level estimate (deferred) subject to the final CI runner profile, and verify against the '[deferred]' value in the spec.

---

## Phase 7: Revision & Robustness (Post-Analysis Fixes)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` review regarding data sourcing, memory constraints, and execution reliability.
**Note**: Strict error handling (T043) and max atoms filter (T044) have been moved to Phase 3 (T048, T014) as they are fundamental data hygiene requirements. T053 and T055 have been merged into Phase 3.

- [ ] T045 [US2] Add a memory-profiling wrapper around the GCN training loop in `code/models/train.py` to log peak RAM usage per epoch, ensuring the process stays within the memory constraint. If memory usage exceeds `MAX_RAM_GB` (defined in `code/config.py`, default GB), trigger an early exit with a diagnostic report.
- [ ] T046 [US3] Update `code/eval/sensitivity.py` to explicitly state the sample size and streaming rules used in the analysis report, ensuring reproducibility of the sensitivity analysis given the chunked processing strategy.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
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