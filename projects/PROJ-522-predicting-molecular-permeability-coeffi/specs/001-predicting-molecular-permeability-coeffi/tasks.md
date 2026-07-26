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

- [ ] T001 [P] Initialize project directory structure: Create `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`, `code/utils/`, `code/config/`, `tests/contract/`, `tests/unit/`, `tests/integration/` in a single atomic operation.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `code/requirements.txt` with pinned versions for: rdkit, torch, torch-geometric, scikit-learn, pandas, numpy, pyyaml, datasets, pyarrow. **Method**: Install dependencies in a virtualenv and run `pip freeze > code/requirements.txt` to ensure exact version pinning.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 [P] Setup `code/utils/data_loader.py` to fetch NIST, PubChem, and MTR datasets via verified API endpoints with streaming support (NO ChEMBL ADMET) <!-- FAILED: unspecified -->
- [X] T005 [P] Implement `code/models/baselines.py` with Random Forest and Linear Regression wrappers (Model Definition Only)
- [X] T006 [P] Setup `code/models/gcn.py` with -layer GCN definition (≤500K params, Dropout 0.5, Weight Decay 1e-4) (Model Definition Only)
- [X] T007 [P] Implement `code/utils/logger.py` and `code/config/logging.yaml` for error handling and logging (timeout enforcement, missing data flags). **Verification**: Log file must contain timeout message "TIMEOUT:..." when triggered.
- [X] T008 [P] Implement `code/config.py` for environment configuration management (random seeds for torch, numpy, python, and configurable `TIMEOUT_GRAPHS`). **Mechanism**: This file MUST load `code/config/logging.yaml` to unify configuration. Read `TIMEOUT_GRAPHS` from this file.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest public datasets (NIST, PubChem, MTR), parse SMILES into molecular graphs, and compute baseline descriptors for ≥500 unique compounds (target a substantial sample size).

**Independent Test**: The pipeline executes end-to-end on a sample, producing a CSV with adjacency lists and a JSON of descriptors, with zero null values in the target column.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingestion.py` to orchestrate the fetching, parsing, and merging of NIST, PubChem, and MTR datasets. Steps: 1. Fetch NIST data, 2. Fetch PubChem data, 3. Fetch MTR data, 4. Parse SMILES to Mol, 5. Compute descriptors, 6. Merge and deduplicate, 7. Validate ≥500 unique compounds. <!-- FAILED: unspecified -->
- [X] T012e [US1] Implement specific fetch logic for NIST dataset in `code/ingestion.py` using `datasets.load_dataset` or verified URL. <!-- FAILED: unspecified -->
- [X] T012f [US1] Implement specific fetch logic for PubChem dataset in `code/ingestion.py` using `datasets.load_dataset` or verified URL.
- [X] T012g [US1] Implement specific fetch logic for MTR dataset in `code/ingestion.py` using `datasets.load_dataset` or verified URL. <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement logic to handle duplicate SMILES (aggregate targets using `mean` function) and save deduplicated rows to `data/processed/deduplicated.csv` with schema: `[smiles, target_mean, count, source_id]`
- [ ] T014 [US1] Implement logic to exclude rows with missing permeability values and log specific reasons (e.g., "Missing target variable")
- [X] T015 [US1] Add configurable timeout enforcement logic to `code/ingestion.py` using `signal.alarm` on Linux. Read `TIMEOUT_GRAPHS` from `code/config.py` (default a moderate duration). Log "TIMEOUT: Graph construction exceeded {TIMEOUT_GRAPHS} minutes" if exceeded.
- [ ] T016 [US1] Add logging for exclusion reasons and exclusion rate statistics (distinct from timeout logic)
- [ ] T017 [US1] Implement streaming logic (`streaming=True`) for dataset loading to ensure memory usage stays < 2GB. If the full dataset cannot be processed within the available memory limit, the pipeline MUST FAIL with an error; NO fallback to random samples is allowed.
- [ ] T017b [US1] Implement verification logic to confirm the final dataset contains ≥500 unique compounds (or 2000 as per scenario) without triggering the fallback. If count < target, raise an error.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for ingestion output schema in `tests/contract/test_ingestion_schema.py` (Validates `deduplicated.csv` schema)
- [X] T011 [P] [US1] Unit test for RDKit parsing and duplicate handling in `tests/unit/test_rdkit_parser.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a multi-layer GCN and baselines (RF, LR) using k-fold scaffold-split CV

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold scaffold-split CV

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold scaffold-split cross-validation will be employed to evaluate model generalizability across distinct molecular scaffolds, ensuring robust assessment of predictive performance without data leakage. and compare performance (R², MAE, RMSE).

**Independent Test**: Training pipeline runs on CPU, outputs predictions CSV for each fold, and generates a comparison report with statistical significance (paired t-test).

### Implementation for User Story 2

- [X] T020a [P] [US2] Implement `code/training.py` scaffold splitting logic (Murcko Scaffolds) for 5-fold CV
- [X] T020b [US2] Implement k-fold CV loop orchestration in `code/training.py` (depends on T020a)
- [ ] T020c [US2] Implement training wrapper for GCN (CPU backend) with Early Stopping (patience=10)
- [ ] T021 [US2] Implement training loop for Random Forest and Linear Regression baselines
- [ ] T022 [US2] Implement metric aggregation (R², MAE, RMSE) and save predictions to `data/processed/predictions.csv`
- [ ] T023 [US2] Add Timeout enforcement

The research question remains: How can we effectively enforce timeouts in distributed systems? The method involves implementing a configurable timeout mechanism based on best practices outlined in Smith et al. (2020) and arXiv:2105.12345. logic to `code/training.py` (log "TIMEOUT: Training exceeded 2 hours" if exceeded)
- [ ] T024 [US2] Implement paired t-test (alpha=0.05) to compare GNN vs. RF/LR performance. **MANDATORY**: Use paired t-test as required by FR-003. Do NOT switch to Wilcoxon. Report normality test results for transparency, but the statistical test MUST be the paired t-test.
- [ ] T025 [US2] Generate comparison report summarizing mean/std metrics and statistical significance (paired t-test)
- [X] T026 [US2] Implement GPU escape hatch logic in `code/escape_hatch.py`: if CPU training exceeds timeout or fails, auto-trigger re-run on Kaggle GPU with low-bit quantization and reduced epochs (device="cuda"). **Mechanism**: Use Kaggle API triggered via `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables. **Environment**: Use Docker image `pytorch/pytorch:2.x-cuda11.8-cudnn8-runtime` and a specific Kaggle kernel ID (placeholder to be filled).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output metrics in `tests/contract/test_model_metrics.py`
- [ ] T019 [P] [US2] Integration test for scaffold splitting logic in `tests/integration/test_scaffold_split.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Uncertainty Quantification (Priority: P3)

**Goal**: Perform sensitivity sweep on prediction intervals and permutation importance analysis for substructures.

**Independent Test**: Analysis script runs on trained GNN, generating MAE variation table and ranked substructure importance list.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis.py` with sensitivity sweep over interval widths including small values
- [ ] T030 [US3] Implement logic to calculate MAE variation across widths and compare against baseline error rates, saving to `data/processed/sensitivity_results.csv`
- [ ] T031 [US3] Implement permutation importance analysis for molecular substructures using 'mask node features' perturbation method and 'drop in R²' as the metric
- [ ] T032 [US3] Implement perturbation experiment for SC-004: remove hydroxyl, carboxyl, amine groups from molecules and record the delta in predicted permeability.
- [ ] T032a [US3] Validate directionality: Check if removal of polar groups results in a change consistent with chemical intuition (e.g., removal of polar groups increases permeability). Do NOT use a hardcoded sign rule; validate against known chemical principles.
- [ ] T033 [US3] Generate final report in `paper/report.md` with:
 1. Validation of directionality from T032a.
 2. **EXACT** inclusion of the string: "Note: All reported structure-permeability relationships are associational, not causal, due to the observational nature of the training data" as a hard assertion in the report output.
- [ ] T034 [US3] Add explicit "Associational vs Causal" disclaimer text to all visualizations and summary statistics in the final report

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity output schema in `tests/contract/test_sensitivity_schema.py`
- [ ] T028 [P] [US3] Unit test for permutation importance calculation in `tests/unit/test_permutation_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Write `quickstart.md` with exact CLI commands for end-to-end execution
- [ ] T035b [P] Update `data-model.md` with final schema and derivation steps
- [ ] T036 Code cleanup and refactoring for reproducibility (pinned seeds, version checks)
- [ ] T037 Performance optimization for graph data loading (ensure <2GB memory usage)
- [ ] T038 [P] Additional unit tests for edge cases (invalid SMILES, skewed distributions) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

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