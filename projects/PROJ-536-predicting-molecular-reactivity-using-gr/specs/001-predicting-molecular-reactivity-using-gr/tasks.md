# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

**Input**: Design documents from `/specs/001-predicting-molecular-reactivity-using-gr/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p src/data src/models src/analysis src/config src/utils tests/contract tests/integration tests/unit` to establish the directory hierarchy.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`: Create file with exact pins (e.g., `rdkit==2023.9.5`, `torch==2.1.0+cpu`, `torch-geometric==2.4.0+cpu`, `scikit-learn==1.3.0`, `pandas==2.1.0`, `numpy==1.24.0`).
- [ ] T003a [P] Add ruff and black to `requirements.txt`: Include `ruff==0.1.0` and `black==23.0.0`.
- [ ] T003b [P] Create `.ruff.toml` and `pyproject.toml` configuration files: Define specific linting rules (e.g., `line-length = 88`, `select = ["E", "F", "W"]`) and formatting settings.
- [ ] T003c [P] Add pre-commit hooks or CI step to run ruff/black: Create `.pre-commit-config.yaml` or CI step to enforce linting.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup configuration management in `src/config/defaults.yaml` (seeds, paths, hyperparameters)
- [ ] T005 [P] Implement custom logging infrastructure in `src/utils/logging.py` to track skipped invalid SMILES
- [ ] T006 [P] Setup metric calculators in `src/utils/metrics.py` (MAE, RMSE, R²)
- [ ] T007 Define and write schema files for `ReactionRecord` and `MolecularGraph` in `specs/001-predicting-molecular-reactivity-using-gr/contracts/`: Create `reaction_record.schema.yaml` (fields: reactants_smiles, product_smiles, yield, reaction_class) and `molecular_graph.schema.yaml` (fields: atoms, bonds, features).
- [ ] T008 Setup CI environment configuration: Create `.github/workflows/ci.yml` with steps for installing dependencies, running tests, and enforcing a strict runtime limit.
- [ ] T009 [P] Create spec amendment request for FR-008: Document the change from "reaction class stratification" to "Scaffold Split" in a formal amendment request or PR description to update `spec.md`. (Note: spec.md has been updated in this revision, this task tracks the workflow).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Yield Prediction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download USPTO subset, parse SMILES to graphs, train lightweight MPNN on CPU, and output regression metrics.

**Independent Test**: Run the full pipeline on a small, fixed subset of USPTO data; verify model file exists and `results/metrics.json` contains finite MAE/RMSE values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Skeleton Unit test for SMILES parsing and invalid entry logging in `tests/unit/test_parsing.py`: Create `test_parse_smiles_invalid_logs_error` function with `pytest.fail` placeholder to verify logging of invalid SMILES.
- [ ] T011 [P] [US1] Skeleton Integration test for MPNN training loop on CPU in `tests/integration/test_pipeline.py`: Create `test_mpnn_training_cpu` function with `pytest.fail` placeholder to verify training loop execution and model saving.

### Implementation for User Story 1

- [ ] T012 [US1] Implement data download in `src/data/download.py` (fetch USPTO subset from verified HuggingFace/Zenodo URL)
- [ ] T013 [US1] Implement schema validation in `src/data/download.py` (Block if 'yield' column missing or categorical)
- [ ] T014 [US1] Implement SMILES-to-Graph conversion in `src/data/parse.py` using RDKit (extract atom/bond features, log invalid entries per FR-001)
- [ ] T014b [US1] Implement data validity calculation in `src/data/parse.py`: Calculate and report the percentage of successfully parsed reactions, asserting it meets the >95% target defined in SC-005.
- [ ] T015 [US1] Implement Molecular Descriptor extraction (MW, logP, TPSA) in `src/data/preprocess.py` for baselines
- [ ] T016a [US1] Implement Scaffold Split logic in `src/data/preprocess.py` (group by MurckoScaffold to prevent leakage)
- [ ] T016b [US1] Create a spec amendment request for FR-008: Draft a formal amendment request or PR description to update `spec.md` to align FR-008 with the Scaffold Split methodology used in the plan.
- [ ] T017 [US1] Implement lightweight MPNN architecture in `src/models/mpnn.py` (CPU-optimized, <1M params, no CUDA)
- [ ] T018 [US1] Implement training loop in `src/analysis/train.py` (Early stopping patience=5, max 200 epochs, MSE loss, save weights; implement K-Fold Cross-Validation as per plan to satisfy FR-003)
- [ ] T019 [US1] Implement inference and metric calculation in `src/analysis/evaluate.py` (Output `results/metrics.json` with MAE, RMSE, R²)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Variance Analysis (Priority: P2)

**Goal**: Compare GNN performance against Random Forest (Morgan fingerprints) and Linear Regression (descriptors), calculate R² improvement, and assess significance.

**Independent Test**: Run comparison module on the same test set; verify report lists R²/MAE/RMSE for all three models and flags practical significance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for baseline model training (RF/LR) in `tests/unit/test_baselines.py`: Create `test_rf_baseline` and `test_lr_baseline` functions with `pytest.fail` placeholders.
- [ ] T021 [P] [US2] Integration test for statistical significance comparison in `tests/integration/test_comparison.py`: Create `test_significance_comparison` function with `pytest.fail` placeholder.

### Implementation for User Story 2

**⚠️ Dependency**: Phase 4 tasks depend on T018 (Model Training) completion.

- [ ] T022 [P] [US2] Implement Random Forest baseline in `src/models/baselines.py` (Morgan fingerprints, scikit-learn)
- [ ] T023 [P] [US2] Implement Linear Regression baseline in `src/models/baselines.py` (MW, logP, TPSA descriptors)
- [ ] T024 [US2] Implement k-Fold Cross-Validation orchestration in `src/analysis/train.py` (Run GNN, RF, LR on same scaffold splits)
- [ ] T025 [US2] Implement metric aggregation and comparison table generation in `src/analysis/evaluate.py`
- [ ] T026 [US2] Implement statistical significance test (paired t-test or Wilcoxon) in `src/analysis/evaluate.py` (Calculate p-value and confidence interval for R² delta)
- [ ] T027 [US2] Implement practical significance assessment logic in `src/analysis/evaluate.py` (Output three states: "Practically Significant" if p < 0.05 AND CI lower bound > 0.10; "Statistically Significant, but effect size uncertain" if p < 0.05 but CI includes 0.10; "No Statistical Significance" if p >= 0.05)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Uncertainty Quantification (Priority: P3)

**Goal**: Identify subgraph patterns using GNNExplainer and generate prediction intervals using Conformal Prediction.

**Independent Test**: Run explainability and uncertainty scripts on trained model; verify ranked motif list and interval CSV with valid bounds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for GNNExplainer output format in `tests/unit/test_explainers.py`: Create `test_gnnexplainer_output` function with `pytest.fail` placeholder.
- [ ] T029 [P] [US3] Unit test for Conformal Prediction interval bounds in `tests/unit/test_uncertainty.py`: Create `test_conformal_bounds` function with `pytest.fail` placeholder.

### Implementation for User Story 3

**⚠️ Dependency**: Phase 5 tasks depend on T018 (Model Training) completion.

- [ ] T030 [US3] Implement GNNExplainer logic in `src/models/explainers.py` (Identify top subgraph motifs, output ranked list as CSV/JSON file, and generate visualizations)
- [ ] T031 [US3] Add mandatory disclaimer to all explainability outputs (ranked list artifact and visualizations) in `src/analysis/viz.py` ("These subgraphs represent associational patterns and may reflect dataset bias; they are not proven causal drivers.") per Plan.md Phase 3 Critical Methodology Update.
- [ ] T032 [US3] Implement Conformal Prediction logic in `src/analysis/uncertainty.py` (Generate lower/upper bounds for test set using Jackknife+ method and calibration set strategy)
- [ ] T033 [US3] Implement coverage rate calculation in `src/analysis/uncertainty.py` (Report % of true yields within intervals)
- [ ] T034 [US3] Validate output artifacts against `contracts/subgraph_pattern.schema.yaml` and `contracts/prediction_interval.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T035 [P] Generate checksums for all raw data and derived artifacts: Compute SHA-256 hashes and write to `data/checksums.txt`.
- [ ] T036 [P] Assemble final report combining logs, metrics, and significance flags
- [ ] T037 [P] Run `quickstart.md` validation: Execute `python -m src.analysis.quickstart --validate` and assert exit code 0, logging output to `logs/quickstart_validation.log`.
- [ ] T038 [P] Implement automated CI runtime check: Add a step in `.github/workflows/ci.yml` that measures total pipeline runtime and fails the build if it exceeds 6 hours, satisfying SC-004.
- [ ] T039 [P] Verify total pipeline runtime is < 6 hours on 2-core CPU runner (SC-004) (Manual verification step for local runs, distinct from T038).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T018 (Model Training) completion** for data splits and model weights.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T018 (Model Training) completion** for model weights.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/parse (T012-T016) MUST precede Model Training (T017-T019)
- Baseline training (T022-T023) MUST precede Comparison (T024-T027)
- GNNExplainer/Conformal (T030-T033) MUST run after model training is complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Baseline models (RF/LR) in US2 can be trained in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Skeleton Unit test for SMILES parsing in tests/unit/test_parsing.py"
Task: "Skeleton Integration test for MPNN training in tests/integration/test_pipeline.py"

# Launch all data prep tasks for User Story 1 together:
Task: "Implement data download in src/data/download.py"
Task: "Implement SMILES-to-Graph conversion in src/data/parse.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify finite MAE/RMSE on CPU)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Baseline comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Explainability)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core Pipeline)
   - Developer B: User Story 2 (Baselines & Stats)
   - Developer C: User Story 3 (Explainability)
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
- **Critical**: Ensure all data processing uses the **Scaffold Split** (T016a) as per plan.md and updated spec.md FR-008.
- **Critical**: Ensure no GPU/CUDA dependencies are introduced; all models must run on CPU-only wheels.
- **Critical**: T009 (Spec Amendment) must be completed before T016a (Scaffold Split implementation) to resolve the spec/plan contradiction.
- **Critical**: T026/T027 must output the nuanced reporting mechanism (three states) per the plan.
- **Critical**: T038 implements the automated CI check for SC-004.