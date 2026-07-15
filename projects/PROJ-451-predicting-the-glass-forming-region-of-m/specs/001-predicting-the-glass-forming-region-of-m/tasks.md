# Tasks: Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

**Input**: Design documents from `/specs/001-gfr-ml-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (`projects/PROJ-451-predicting-the-glass-forming-region-of-m/`) per `plan.md` <!-- ATOMIZE: requested -->
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, xgboost, pandas, numpy, shap, scipy, requests, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `utils/io.py` with functions for loading CSV/JSON data and handling Materials Project API requests (API Key via env var, v3 endpoint)
- [ ] T005 [P] Implement `utils/dedup.py` for deduplicating compositions by unique chemical formula (normalized atomic fractions), {{claim:c_6a2d6a3c}} (Wikidata Q19881044, https://www.wikidata.org/wiki/Q19881044)
- [ ] T006 Create `data/provenance.json` schema for tracking source URLs (Zenodo) and checksums
- [ ] T007 [P] Setup `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [ ] T008 Configure environment configuration management for API keys (Materials Project) and dataset paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Load alloy composition data from Science Advances and Materials Project, compute atomic-scale descriptors, and output a structured dataset.

**Independent Test**: Verify output dataset contains ≥1000 alloy compositions with ≥10 computed descriptors, and descriptor values fall within physically reasonable ranges (e.g., atomic size mismatch ∈ [non-negative, ]).

### Implementation for User Story 1

- [ ] T009 [P] [US1] Write unit test for `features/descriptors.py` in `tests/unit/test_descriptors.py` (verify formula correctness for the specific descriptors: Atomic Radius, Electronegativity, Valence Electron Concentration, Atomic Size Mismatch, Mixing Enthalpy, Atomic Size Difference, Valence Electron Size Mismatch, Electron-Atom Ratio, Miedema's Heat of Formation, and Atomic Packing Factor). **Note**: This is a TDD 'write test' task; expect initial failure.
- [ ] T010 [P] [US1] Write unit test for `utils/dedup.py` in `tests/unit/test_dedup.py` (verify deduplication logic and source retention). **Note**: This is a TDD 'write test' task; expect initial failure.
- [~] T012 [P] [US1] Create `features/descriptors.py` to compute a set of atomic descriptors: Atomic Radius, Electronegativity, Valence Electron Concentration, Atomic Size Mismatch (δ), Mixing Enthalpy (ΔHmix), Atomic Size Difference, Valence Electron Size Mismatch, Electron-Atom Ratio, Miedema's Heat of Formation, and Atomic Packing Factor. Ensure all formulas are implemented and documented.
- [~] T013 [US1] Implement data ingestion script `code/main.py` (or `scripts/ingest.py`) to fetch from Zenodo DOI and Materials Project API (v3, API Key via env, fields: composition, phase, elemental properties), merging records. **Constraint**: If the primary DOI source is unavailable, MUST fallback to the synthetic generator (T013b) to ensure reproducibility per plan.md.
- [~] T013b [US1] Implement synthetic data generator `utils/synthetic.py` to generate valid alloy compositions with realistic descriptors when canonical DOI is unavailable (supports reproducibility per plan.md Constitution Check).
- [X] T011 [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py` (Requires T013 completion).
- [~] T014 [US1] Implement label filtering in `utils/io.py` to exclude compositions lacking definitive phase labels (amorphous/crystalline) per FR-009
- [~] T015 [US1] Implement dataset capping logic in `utils/io.py` to enforce ≤10,000 compositions limit per FR-007 using **stratified random sampling** by alloy system. This task ensures the hard cap is met before training.
- [ ] T016 [US1] Generate `data/processed/engineered_dataset.csv` with all required descriptors and metadata
- [~] T017 [US1] Add validation checks to ensure ≥95% descriptor completeness and drop compositions with missing elemental properties

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Performance Validation (Priority: P2)

**Goal**: Train Random Forest and XGBoost classifiers with k-fold cross-validation, compare against logistic regression baseline, and perform statistical significance testing.

**Independent Test**: Verify system calculates balanced accuracy, precision, recall, F1-score for all models, and executes paired t-test to report p-values.

### Implementation for User Story 2

- [X] T019 [P] [US2] Write unit test for model training loop in `tests/unit/test_training.py` (verify stratified split logic). **Note**: This is a TDD 'write test' task; expect initial failure.
- [ ] T020 [US2] Create `models/train.py` with stratified k-fold cross-validation logic (stratify by alloy system, derived by extracting primary base element via regex).
- [ ] T021 [P] [US2] Implement Random Forest classifier training with hyperparameter optimization (grid search or randomized search) within `models/train.py`
- [ ] T022 [P] [US2] Implement XGBoost classifier training with hyperparameter optimization within `models/train.py`
- [ ] T023 [P] [US2] Implement Logistic Regression baseline training in `models/train.py`
- [ ] T024 [US2] Implement metrics calculation (balanced accuracy, precision, recall, F1) in `models/evaluate.py`
- [ ] T026 [US2] Implement Bonferroni correction logic for multiple hypothesis testing per FR-008 in `utils/stats.py`. **Mandatory**: This logic must be available before T025.
- [ ] T025 [US2] Implement **paired t-test** (using `scipy.stats.ttest_rel`) to compare RF/XGBoost vs. baseline, reporting p-values. **Mandatory**: Apply Bonferroni correction (from T026) as the primary method for multiple hypothesis testing per FR-008.
- [ ] T027 [US2] Generate `data/results/model_performance_metrics.json` with all fold-level scores and aggregate metrics
- [ ] T028 [US2] Add logic to handle edge cases: insufficient samples per alloy system for stratification (fallback to simple split or warning)
- [ ] T030 [P] [US2] Write unit test for 80/20 split logic in `tests/unit/test_split.py`. **Note**: This is a TDD 'write test' task; expect initial failure.
- [ ] T029 [US2] Apply /20 stratified train/test split logic in `models/train.py` (stratify by alloy system) to satisfy FR-003. **Note**: This task resolves the [deferred] status in FR-003 by defining the implementation logic ([deferred] train, [deferred] test).
- [ ] T031 [US2] Apply Bonferroni correction to final p-values in `model_performance_metrics.json` and update metrics
- [ ] T032 [US2] Integration test for full training pipeline in `tests/integration/test_training_pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Visualization (Priority: P3)

**Goal**: Extract permutation importance and generate SHAP plots to explain model predictions.

**Independent Test**: Verify SHAP plots are generated for the top-ranked descriptors and permutation importance scores are non-negative and sum to unity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for SHAP value computation in `tests/unit/test_interpretability.py`
- [ ] T034 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement permutation importance calculation in `models/evaluate.py`
- [ ] T036 [US3] Implement SHAP value computation for the trained Random Forest model in `models/evaluate.py`
- [ ] T037 [US3] Generate SHAP summary plot for top descriptors using `matplotlib`/`seaborn` and save to `data/results/shap_summary.png`
- [ ] T038 [US3] Generate feature importance bar chart (top descriptors) and save to `data/results/feature_importance.png`
- [ ] T039 [US3] Write interpretability report to `data/results/interpretability_report.md` summarizing key physical drivers

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates: `quickstart.md` (setup, run, data sources)
- [ ] T041 [P] Documentation updates: `research.md` (methodology, results, statistical tests)
- [ ] T042 Code cleanup and refactoring in `code/`
- [ ] T043 Performance optimization for CPU-only execution (ensure no GPU calls, optimize memory usage)
- [ ] T044 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T045 Verify all artifacts (datasets, models, plots) are checksummed in `data/provenance.json`

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/engineered_dataset.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models from `models/train.py`)

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
Task: "Write unit test for features/descriptors.py in tests/unit/test_descriptors.py"
Task: "Write unit test for utils/dedup.py in tests/unit/test_dedup.py"

# Launch all models for User Story 1 together:
Task: "Create features/descriptors.py to compute atomic size mismatch..."
Task: "Implement data ingestion script code/main.py..."
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
 - Developer B: User Story 2 (waiting for US1 data)
 - Developer C: User Story 3 (waiting for US2 models)
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
- **Critical Constraint**: All data ingestion must use real sources (Zenodo DOI or Materials Project API); synthetic data is ONLY a fallback when the DOI is unavailable (T013b).
- **Critical Constraint**: All models must run on CPU-only CI with limited cores and memory; no GPU/CUDA dependencies.
- **Critical Constraint**: Dataset must be capped using stratified random sampling to preserve statistical validity (T015).
- **Critical Constraint**: All 10 descriptors must be computed and verified (T012, T009).
- **Critical Constraint**: Paired t-test must be the primary statistical test; Bonferroni correction is mandatory for multiple comparisons (T025, T026).
- **Critical Constraint**: Bonferroni correction must be applied to final p-values (T031).