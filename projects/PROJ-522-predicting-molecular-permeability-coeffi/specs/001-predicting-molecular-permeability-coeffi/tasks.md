# Tasks: Predicting Molecular Permeability Coefficients via Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-permeability/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Initialize project directory structure: Create `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`, `code/utils/`, `code/config/`, `tests/contract/`, `tests/unit/`, `tests/integration/`. **Deliverable**: Create `code/requirements.txt`, `code/setup.py`, `code/pyproject.toml` files to define the project root structure.
- [ ] T001b [P] Create `__init__.py` files in all `code/` and `tests/` subdirectories to make them Python packages.
- [ ] T001c [P] Create `.gitkeep` files in all `data/` subdirectories to preserve directory structure in version control.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `code/requirements.txt` with pinned versions for: rdkit, torch, torch-geometric, scikit-learn, pandas, numpy, pyyaml, datasets, pyarrow. **Method**: Install dependencies in a virtualenv and run `pip freeze > code/requirements.txt` to ensure exact version pinning.
- [X] T003 [P] Create `code/.ruff.toml` with linting rules (max-line-length=100, ignore=E501) and `code/.black.toml` with formatting rules (line-length=100). **Deliverable**: Both config files must exist and be valid.
- [X] T004 [P] Setup `code/utils/data_loader.py` to define the **MultiSourceDataLoader** interface for NIST, PubChem, and MTR datasets. **Constraint**: NO fallback to synthetic data. If fetch fails, raise an error immediately. This task defines the interface; T012a implements the fetch. **Deliverable**: `code/utils/data_loader.py` with `MultiSourceDataLoader` class and abstract methods for `fetch_nist`, `fetch_pubchem`, `fetch_mtr`.
- [X] T005 [P] Implement `code/models/baselines.py` with Random Forest and Linear Regression wrappers (Model Definition Only)
- [X] T006 [P] Setup `code/models/gcn.py` with **3-layer** GCN definition (≤500K params, Dropout 0.5, Weight Decay 1e-4) (Model Definition Only)
- [X] T007 [P] Implement `code/utils/logger.py` and `code/config/logging.yaml` for error handling and logging (timeout enforcement, missing data flags). **Verification**: Log file must contain timeout message "TIMEOUT:..." when triggered.
- [X] T008 [P] Implement `code/config.py` for environment configuration management (random seeds for torch, numpy, python, and configurable `TIMEOUT_GRAPHS`). **Mechanism**: This file MUST load `code/config/logging.yaml` to unify configuration. Read `TIMEOUT_GRAPHS` from this file. **Default**: 300 seconds (5 minutes).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest public datasets (NIST, PubChem, MTR), parse SMILES into molecular graphs, and compute baseline descriptors for ≥500 unique compounds.

**Independent Test**: The pipeline executes end-to-end on a sample, producing a CSV with adjacency lists and a JSON of descriptors, with zero null values in the target column.

### Implementation for User Story 1

- [ ] T012a [US1] Implement `code/ingestion.py` to fetch **NIST, PubChem, and MTR** datasets via `datasets.load_dataset` or specific API calls. **Dependency**: T004. **Output**: Raw data in `data/raw/nist.parquet`, `data/raw/pubchem.parquet`, `data/raw/mtr.parquet`.
- [X] T012b [US1] Implement `code/ingestion.py` to parse SMILES to Mol using RDKit and compute descriptors (MW, logP, PSA, rotatable bonds). **Output**: Intermediate dataframe in memory.
- [ ] T012c [US1] Implement `code/ingestion.py` to handle duplicate SMILES (aggregate targets using `mean` function) and save deduplicated rows to `data/processed/deduplicated.csv` with schema: `[smiles, target_mean, count, source_id]`. **Function**: `deduplicate_smiles(df)`.
- [ ] T012d [US1] Implement `code/ingestion.py` to validate ≥500 unique compounds, exclude rows with missing permeability values, log exclusion reasons to `data/processed/exclusion_log.json`, and output `data/processed/validation_report.json` containing the count and status. **Constraint**: If count < 500, raise an error.
- [~] T012e [US1] Implement `code/ingestion.py` to merge NIST, PubChem, and MTR datasets into a single `data/processed/merged_dataset.csv`. **Function**: `merge_sources(df_nist, df_pubchem, df_mtr)`.
- [ ] T014 [US1] Implement logic to exclude rows with missing permeability values and log specific reasons (e.g., "Missing target variable") to `data/processed/exclusion_log.json`. **Artifact**: `data/processed/exclusion_log.json` with schema `[{"smiles": "...", "reason": "..."}]`.
- [X] T015 [US1] Add configurable timeout enforcement logic to `code/ingestion.py` using `signal.alarm` on Linux. Read `TIMEOUT_GRAPHS` from `code/config.py` (default 300 seconds). Log "TIMEOUT: Graph construction exceeded 5 minutes" if exceeded.
- [ ] T016 [US1] Add logging for exclusion reasons and exclusion rate statistics to `data/processed/exclusion_stats.json`. **Artifact**: `data/processed/exclusion_stats.json` with schema `{"total_rows": int, "excluded_rows": int, "rate": float}`.
- [~] T017 [US1] Implement streaming logic (`streaming=True`) for dataset loading to ensure memory usage stays < 2GB. **Constraint**: If the full dataset cannot be processed within the available memory limit, the pipeline MUST FAIL with an error; NO fallback to random samples or synthetic data is allowed within this script.
- [~] T017e [US1] **GPU ESCAPE HATCH**: Implement `code/escape_hatch.py` to re-run ingestion on a generic GPU runner (if available) using environment variables. **Output**: `data/processed/escape_hatch_log.json` with schema `{"triggered": bool, "runner_type": "gpu", "status": "success|fail"}`. **Constraint**: No Kaggle API or kernel IDs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for ingestion output schema in `tests/contract/test_ingestion_schema.py` (Validates `deduplicated.csv` schema)
- [X] T011 [P] [US1] Unit test for RDKit parsing and duplicate handling in `tests/unit/test_rdkit_parser.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a multi-layer GCN and baselines (RF, LR) using k-fold scaffold-split CV

**Independent Test**: Training pipeline runs on CPU, outputs predictions CSV for each fold, and generates a comparison report with statistical significance (paired t-test).

### Implementation for User Story 2

- [X] T020c [US2] Implement training wrapper for GCN (CPU backend) with Early Stopping (patience=10) in `code/models/gcn.py::GCNWrapper`. **Output**: `tests/unit/test_gcn_training.py` must pass. **Signature**: `class GCNWrapper(torch.nn.Module)`.
- [~] T021 [US2] Implement training loop for Random Forest and Linear Regression baselines in `code/models/baselines.py::BaselineTrainer`. **Output**: Save baseline predictions to `data/processed/baseline_predictions.csv`. **Signature**: `class BaselineTrainer`. **Schema**: `[fold, model, prediction, target]`.
- [X] T020b [US2] Implement k-fold CV loop orchestration in `code/training.py` (depends on T020c, T021).
- [~] T022a [US2] Implement metric aggregation (R², MAE, RMSE) function `code/utils/metrics.py::aggregate_metrics`. **Output**: `data/processed/metrics_summary.csv`. **Schema**: `[fold, model, r2, mae, rmse]`.
- [ ] T022b [US2] Save predictions to `data/processed/predictions.csv` with columns [fold, model, r2, mae, rmse, prediction, target].
- [X] T023 [US2] Add Timeout enforcement logic to `code/training.py` using `signal.alarm` wrapper `run_training_with_timeout`. Log "TIMEOUT: Training exceeded 5 minutes" if exceeded.
- [ ] T024 [US2] Implement **paired t-test** (alpha=0.05) to compare GNN vs. RF/LR performance. **Fallback**: If normality assumption fails, implement Wilcoxon signed-rank test as secondary. **Output**: Append p-value and test statistic to `data/processed/statistical_comparison.csv`. **Schema**: `[fold, model, p_value, statistic]`.
- [ ] T025a [US2] Generate comparison report in `paper/report.md` summarizing mean/std metrics and statistical significance (t-test). **Constraint**: Ensure `paper/report.md` contains the exact string: "Statistical comparison used paired t-test (alpha=0.05) as per Spec FR-003. Wilcoxon used only as fallback if normality fails."
- [ ] T026 [US2] **GPU ESCAPE HATCH**: Implement `code/escape_hatch.py` to re-run training on a generic GPU runner (if available) using environment variables. **Output**: `data/processed/escape_hatch_log.json`. **Constraint**: No Kaggle API or kernel IDs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output metrics in `tests/contract/test_model_metrics.py`
- [ ] T019 [P] [US2] Integration test for scaffold splitting logic in `tests/integration/test_scaffold_split.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Uncertainty Quantification (Priority: P3)

**Goal**: Perform sensitivity sweep on prediction intervals and permutation importance analysis for substructures.

**Independent Test**: Analysis script runs on trained GNN, generating MAE variation table and ranked substructure importance list.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis.py::sensitivity_sweep` with sensitivity sweep over a range of interval widths. **Output**: Write `data/processed/sensitivity_sweep.csv` with columns [width, mae, ci]. **Signature**: `def sensitivity_sweep(model, data, widths)`.
- [ ] T030 [US3] Implement logic to calculate MAE variation across widths and compare against baseline error rates, saving to `data/processed/sensitivity_results.csv` with columns: [width, mae, baseline_mae, delta].
- [ ] T031 [US3] Implement permutation importance analysis for molecular substructures using 'mask node features' perturbation method and 'drop in R²' as the metric. **Output**: Save ranked substructures to `data/processed/permutation_importance.csv` with columns [substructure, importance_score]. **Signature**: `def permutation_importance(model, data)`.
- [ ] T032 [US3] **SC-004 IMPLEMENTATION**: Implement a perturbation experiment that **chemically removes** specific functional groups (hydroxyl, carboxyl, amine) from molecules using RDKit reaction rules and records the delta in predicted permeability.
- [ ] T032b [US3] Define chemical intuition reference logic: Create `code/config/chemical_intuition.json` with expected permeability changes for hydroxyl, carboxyl, amine removal. **Schema**: `{"group": str, "expected_direction": "increase|decrease"}`.
- [ ] T032a [US3] Validate directionality: Check if removal of polar groups results in a change consistent with chemical intuition (e.g., removal of polar groups increases permeability). **Output**: Write a validation status to `data/processed/chemical_intuition_check.json` with keys [status, observed_delta, expected_direction].
- [ ] T033a [US3] Generate validation results in `data/processed/validation_results.json`. **Schema**: `{"passed": bool, "details": str}`.
- [ ] T033b [US3] Ensure `paper/report.md` contains a section titled "Domain Shift" with the text: "This study uses NIST, PubChem, and MTR data for polymeric membrane permeability. All results are interpreted within the context of polymeric membranes."
- [ ] T033c [US3] Ensure `paper/report.md` contains the exact string: "Note: All reported structure-permeability relationships are associational, not causal, due to the observational nature of the training data" as a hard assertion in the report output.
- [ ] T034 [US3] Add explicit "Associational vs Causal" disclaimer text to all visualizations and summary statistics. **Implementation Details**:
 1. In `code/analysis.py`: Modify all `plt.title()`, `plt.xlabel()`, and `plt.ylabel()` calls in the sensitivity and permutation plots to append the string " (Note: Associational, not causal)" or include a text box with the full disclaimer: "Note: All reported structure-permeability relationships are associational, not causal, due to the observational nature of the training data."
 2. In `code/report.py`: Modify the generation of summary statistic tables to include a footer row or caption with the exact string: "Note: All reported structure-permeability relationships are associational, not causal, due to the observational nature of the training data."
 3. Ensure `paper/report.md` and `data/processed/figures/` output files (if saved as images with metadata) contain this disclaimer in their captions or accompanying sidecar JSON files.
- [ ] T035a [P] Write `quickstart.md` with exact CLI commands:
 1. `python code/ingestion.py --source nist,pubchem,mtr --output data/processed/merged_dataset.csv`
 2. `python code/training.py --input data/processed/merged_dataset.csv --output data/processed/predictions.csv --model_path data/models/gcn_model.pt`
 3. `python code/analysis.py --model_path data/models/gcn_model.pt --data_path data/processed/merged_dataset.csv --output data/processed/sensitivity_results.csv`
 **Deliverable**: Include environment setup steps (e.g., `export PYTHONPATH=...`) and dependency installation commands.
- [ ] T035b [P] Update `data-model.md` with a "Derived Data" table containing columns [file, source, derivation]. **Deliverable**: Add table to `data-model.md`.
- [ ] T036 [P] Code cleanup and refactoring for reproducibility: Run `ruff check` and fix all errors; ensure all seeds are set in `code/config.py`. **Deliverable**: `ruff check` passes with 0 errors.
- [ ] T037 [P] Performance optimization for graph data loading: Run `memory-profiler` and log output to `data/processed/memory_report.json` to ensure <2GB memory usage. **Deliverable**: `data/processed/memory_report.json` with peak memory usage.
- [ ] T038 [P] Additional unit tests for edge cases: Add `tests/unit/test_invalid_smiles.py::test_handles_malformed_input`, `tests/unit/test_skewed_distribution.py::test_handles_skewed_data`. **Deliverable**: Tests pass.
- [ ] T039 [P] Run `quickstart.md` validation and generate `validation_log.txt` with exit code 0. **Deliverable**: `validation_log.txt` with "SUCCESS" and exit code 0.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity output schema in `tests/contract/test_sensitivity_schema.py`
- [ ] T028 [P] [US3] Unit test for permutation importance calculation in `tests/unit/test_permutation_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Code cleanup and refactoring for reproducibility (pinned seeds, version checks)
- [ ] T037 [P] Performance optimization for graph data loading (ensure <2GB memory usage)
- [ ] T038 [P] Additional unit tests for edge cases (invalid SMILES, skewed distributions) in `tests/unit/`
- [ ] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

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
# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/ingestion.py to fetch NIST, PubChem, MTR datasets..."
Task: "Implement code/ingestion.py to parse SMILES to Mol objects..."
Task: "Implement graph construction to generate adjacency lists..."

# Launch tests after implementation schema is defined:
Task: "Contract test for ingestion output schema..."
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