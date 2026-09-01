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

- [ ] T001a [P] Create root directory structure (`projects/PROJ-451-predicting-the-glass-forming-region-of-m/`) per `plan.md` <!-- FAILED: unspecified -->
- [ ] T001b [P] Create `code/`, `data/`, `tests/`, `docs/`, `notebooks/` subdirectories
- [X] T001c [P] Initialize Python 3.11 project with `requirements.txt` (scikit-learn, xgboost, pandas, numpy, shap, scipy, requests, pytest)
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] [US1] Implement `utils/dedup.py` for deduplicating compositions by unique chemical formula. **Algorithm**: Normalize formula to Hill system (C first, then H, then alphabetical), sort elements, compare strings. **Output**: `data/processed/deduped_compositions.csv`. Retain records from primary source (Science Advances) if duplicates exist (FR-010).
- [X] T004 [P] Create `data/provenance.json` schema for tracking source URLs (Zenodo) and checksums
- [ ] T005 [P] Setup `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [ ] T006 [P] Configure environment configuration management. **Deliverables**: Create `.env.example` with placeholders for `MATERIALS_PROJECT_API_KEY` and `DATA_PATH`; create `utils/config.py` to load and validate these keys from `.env` or environment variables.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Load alloy composition data from Science Advances and Materials Project, compute atomic-scale descriptors, and output a structured dataset.

**Independent Test**: verify output dataset contains ≥1000 alloy compositions with ≥10 computed descriptors, and descriptor values fall within physically reasonable ranges (e.g., atomic size mismatch ∈ [non-negative, 1], electronegativity difference ∈ [non-negative, 3]).

### Implementation for User Story 1

- [X] T007 [P] [US1] Write unit test for `features/descriptors.py` in `tests/unit/test_descriptors.py` (verify formula correctness for the specific descriptors: Atomic Radius, Electronegativity, Valence Electron Concentration, Atomic Size Mismatch, Mixing Enthalpy, etc.). **Note**: This is a TDD 'write test' task; expect initial failure.
- [X] T008 [P] [US1] Write unit test for `utils/dedup.py` in `tests/unit/test_dedup.py` (verify deduplication logic and source retention). **Note**: This is a TDD 'write test' task; expect initial failure.
- [X] T009 [P] [US1] Create `features/descriptors.py` to compute atomic descriptors. **Core (Mandatory)**: Atomic Size Mismatch (δ), Electronegativity Difference (Δχ), Mixing Enthalpy (ΔHmix). **Optional (Extension)**: Atomic Radius, Valence Electron Concentration, etc. **Reference**: Use formulas and constants defined in `docs/thermodynamics.md`.
- [ ] T010 [US1] Implement data ingestion script `scripts/ingest.py` to fetch from Zenodo DOI `10.1126/sciadv.aaq1566` (file: `alloy_data.csv`) and Materials Project API (v3, API Key via env, fields: composition, phase, elemental properties). **Constraint**: If the primary DOI source is unavailable, the script MUST raise a `ValueError` immediately. Synthetic data (T011) is NOT a fallback for the main pipeline; it is a separate local testing tool.
- [ ] T011 [US1] Implement synthetic data generator `utils/synthetic.py` to generate valid alloy compositions with realistic descriptors for local testing and reproducibility verification when the canonical DOI is inaccessible. **Note**: This is a parallel task to T010, not a fallback.
- [X] T012 [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py` (Requires T010 and T011 completion).
- [ ] T013 [US1] Implement label filtering in `scripts/ingest.py` or `utils/io.py` to exclude compositions lacking definitive phase labels (amorphous/crystalline) per FR-009. **Output**: `data/processed/filtered_dataset.csv`.
- [ ] T014 [US1] Implement dataset capping logic in `scripts/ingest.py` to enforce ≤10,000 compositions limit per FR-007 using **stratified random sampling** by alloy system. **Priority**: Retain records from primary source (Science Advances) first (FR-010). **Logic**: Use 'primary base element' derivation from T020 for stratification.
- [ ] T015 [US1] Generate `data/processed/engineered_dataset.csv` with all required descriptors and metadata.
- [ ] T016 [US1] Add validation checks to ensure ≥95% descriptor completeness and drop compositions with missing elemental properties. **Output**: `data/processed/completeness_report.json`.
- [ ] T017 [US1] Implement strict error handling in `utils/io.py` for elemental property lookups: if a required property (e.g., electronegativity for a rare earth) is missing, the script MUST raise a `ValueError` immediately rather than dropping the row silently or imputing a default value, ensuring data hygiene per FR-001.
- [ ] T018 [US1] Implement streaming/iterative processing in `scripts/ingest.py` to handle large datasets **ONLY IF** size > 10,000 rows, otherwise load into memory. This ensures compliance with the 7 GB RAM constraint in FR-007 as a safety measure.

---

## Phase 4: User Story 2 - Model Training and Performance Validation (Priority: P2)

**Goal**: Train Random Forest and XGBoost classifiers with k-fold cross-validation, compare against logistic regression baseline, and perform statistical significance testing.

**Independent Test**: Verify system calculates balanced accuracy, precision, recall, F1-score for all models, and executes paired t-test to report p-values.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Write unit test for model training loop in `tests/unit/test_training.py` (verify stratified split logic). **Note**: This is a TDD 'write test' task; expect initial failure.
- [ ] T020 [US2] Create `models/train.py` with stratified k-fold cross-validation logic. **Stratification Logic**: Extract 'primary base element' via regex (e.g., match the most abundant element or the first element in Hill order) to define 'alloy system'.
- [ ] T021 [P] [US2] Implement Random Forest classifier training with hyperparameter optimization (grid search or randomized search) within `models/train.py`
- [ ] T022 [P] [US2] Implement XGBoost classifier training with hyperparameter optimization within `models/train.py`
- [ ] T023 [P] [US2] Implement Logistic Regression baseline training in `models/train.py`
- [ ] T024 [US2] Implement metrics calculation (balanced accuracy, precision, recall, F1) in `models/evaluate.py`
- [ ] T025 [US2] Implement **Bonferroni correction** logic for multiple hypothesis testing per FR-008 in `utils/stats.py`. **Mandatory**: This logic must be available before T026.
- [ ] T026 [US2] Implement **paired t-test** (using `scipy.stats.ttest_rel`) to compare RF/XGBoost vs. baseline, reporting p-values. **Input**: Fold-level scores from T027 (or T024). **Output**: Append p-values to `data/results/model_performance_metrics.json`. Apply Bonferroni correction (from T025) as the primary method for multiple hypothesis testing per FR-008.
- [ ] T027 [US2] Add logic to handle edge cases: insufficient samples per alloy system for stratification (fallback to simple split or warning)
- [ ] T028 [US2] Write unit test for split logic in `tests/unit/test_split.py`. **Note**: This is a TDD 'write test' task; expect initial failure.
- [ ] T029 [US2] Apply stratified train/test split logic in `models/train.py` (stratify by alloy system) to satisfy FR-003. **Logic**: Determine split ratio based on class balance and alloy system distribution (deferred, not hardcoded to 80/20).
- [ ] T030 [US2] Apply Bonferroni correction to final p-values in `data/results/model_performance_metrics.json` and update metrics. **Note**: Must run before T031 to ensure the generated artifact contains corrected values.
- [ ] T031 [US2] Generate `data/results/model_performance_metrics.json` with all fold-level scores and aggregate metrics (including corrected p-values).
- [ ] T032 [US2] Integration test for full training pipeline in `tests/integration/test_training_pipeline.py`
- [ ] T033 [US2] Add explicit handling for the boundary condition where p = 0.05 exactly in `utils/stats.py`: the system MUST report the exact p-value and a specific status flag (e.g., "boundary_significance") rather than a binary pass/fail, ensuring scientific rigor per the edge case analysis in spec.md.
- [ ] T034 [US2] Ensure `models/train.py` enforces `device="cpu"` explicitly in all model initializations (RF, XGBoost, LR) to prevent accidental GPU usage and ensure compatibility with the 2-core CPU runner constraint.

---

## Phase 5: User Story 3 - Interpretability and Visualization (Priority: P3)

**Goal**: Extract permutation importance and generate SHAP plots to explain model predictions.

**Independent Test**: Verify SHAP plots are generated for the top-ranked descriptors and permutation importance scores are non-negative and sum to unity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for SHAP value computation in `tests/unit/test_interpretability.py`
- [ ] T036 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz.py`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement permutation importance calculation in `models/evaluate.py`
- [ ] T038 [US3] Implement SHAP value computation for the trained Random Forest model in `models/evaluate.py`
- [ ] T039 [US3] Generate SHAP summary plot for top descriptors using `matplotlib`/`seaborn` and save to `data/results/shap_summary.png`
- [ ] T040 [US3] Generate feature importance bar chart (top descriptors) and save to `data/results/feature_importance.png`
- [ ] T041 [US3] Write interpretability report to `data/results/interpretability_report.md`. **Sections**: 1. Executive Summary, 2. Top 3 Physical Drivers (with % contribution), 3. SHAP Analysis of Key Descriptors, 4. Implications for Alloy Design.
- [ ] T042 [US3] Implement validation logic in `models/evaluate.py` to verify that permutation importance scores are normalized (sum to 1.0) and non-negative before saving results, ensuring compliance with the acceptance criteria in US-3.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates: `quickstart.md` (setup, run, data sources)
- [ ] T044 [P] Documentation updates: `research.md` (methodology, results, statistical tests)
- [ ] T045 Code cleanup and refactoring in `code/`
- [ ] T046 [P] Performance optimization for CPU-only execution (ensure no GPU calls, optimize memory usage)
- [ ] T047 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T048 [P] Verify all artifacts (datasets, models, plots) are checksummed in `data/provenance.json`

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
Task: "Implement data ingestion script scripts/ingest.py..."
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
- **Critical Constraint**: All data ingestion must use real sources (Zenodo DOI or Materials Project API); synthetic data is ONLY for local testing (T011), not a fallback for the main pipeline (T010).
- **Critical Constraint**: All models must run on CPU-only CI with limited cores and memory; no GPU/CUDA dependencies.
- **Critical Constraint**: Dataset must be capped using stratified random sampling to preserve statistical validity (T014), retaining primary source records first.
- **Critical Constraint**: All 10 descriptors are computed, but only 3 (size mismatch, electronegativity, mixing enthalpy) are mandatory per spec (T009).
- **Critical Constraint**: Paired t-test must be the primary statistical test; Bonferroni correction is mandatory for multiple comparisons (T025, T026).
- **Critical Constraint**: Bonferroni correction must be applied to final p-values before generating metrics (T030, T031).
- **Critical Constraint**: Data loaders must fail loudly on missing elemental properties (T017) and stream only if dataset > 10k rows (T018) to ensure data integrity and resource compliance.
- **Critical Constraint**: Statistical tests must handle boundary conditions explicitly (T033).
