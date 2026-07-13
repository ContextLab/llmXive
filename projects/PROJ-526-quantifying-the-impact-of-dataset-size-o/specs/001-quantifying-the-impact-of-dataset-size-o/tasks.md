# Tasks: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-dataset-size-o/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root directories: `projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/`, `code/`, `data/`, `tests/`, `state/`, `docs/`
- [ ] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `tests/contract/`, `tests/unit/`, `tests/integration/`
- [ ] T001c [P] Initialize git repository and create `.gitignore` for Python/data artifacts

---

## Phase 2: Foundational (Blocking Prerequisites & Legal Amendments)

**Purpose**: Core infrastructure AND the legal amendments required to proceed with feasibility adjustments.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Amendments (T035, T036) MUST precede implementation tasks (T019, T020, T027).**

- [ ] T002 Initialize Python 3.10 project with dependencies (`pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`) in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [ ] T004 Create `data/` directory structure (`raw/`, `processed/`) and `state/` for checksums
- [~] T005 [P] Implement data integrity utilities: `sha256` checksumming and logging in `code/utils/integrity.py`
- [~] T006 [P] Setup environment configuration management for API keys and paths in `code/config.py`
- [~] T007 Create base data models (MaterialEntry, LearningCurve, ScalingResult) in `code/models.py`
- [~] T008 Configure deterministic seed setting for `numpy` and `random` in `code/utils/seed.py`
- [~] T035 [P] **Amendment Task**: Create a formal amendment record in `state/amendments.md` documenting the deviation from Constitution Principle VII (reduced subsets/seeds) and the data availability constraint (properties -> N=2-3). This amendment is a prerequisite for T019, T020, T027.
- [~] T036 [P] **Amendment Task**: Update `spec.md` (and `state/amendments.md`) to formally modify Success Criterion SC-001 baseline to reflect the actual N (2-3) instead of 15, and update the statistical protocol to mandate Permutation Test for N<5. This amendment is a prerequisite for T027.

**Checkpoint**: Foundation and Legal Amendments ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Composition Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Download standardized material property datasets from public repositories and compute composition-only descriptors (Magpie vectors) to establish a baseline.

**Independent Test**: Verify that the pipeline retrieves data for available properties, computes Magpie features without structural data, and outputs a consolidated Parquet file passing schema validation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [~] T010 [P] [US1] Unit test for Magpie vector generation (no structural features) in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/download_data.py` to fetch materials data from HuggingFace (Materials Project/AFLOW) with exponential backoff for rate limits
- [~] T012 [US1] Implement `code/generate_descriptors.py` to compute Magpie composition-only descriptors for all entries
- [~] T013 [US1] Implement data consolidation logic to merge properties into a single `data/processed/materials_master.parquet` file (with CSV fallback if memory permits)
- [~] T014 [US1] Implement chunked loading in `code/download_data.py` using batch processing and optimized dtypes (float32) to verify peak RAM usage remains < 7GB during full dataset load
- [ ] T015 [US1] Add logging for download progress and descriptor generation stats
- [ ] T016 [US1] Implement validation logic to count distinct properties. **IF count < 15, raise a critical `ValueError` and halt the pipeline immediately.** Log the "15-N" gap and update `state/properties_status.json` ONLY if the count is sufficient. This task enforces the hard constraint of FR-001; execution must not proceed to US2/US3 if this check fails.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Learning Curve Construction and Scaling Analysis (Priority: P2)

**Goal**: Generate learning curves for each property by training Random Forest regressors on varying subset sizes, fit power-law models, and extract scaling exponents.

**Independent Test**: Verify that learning curves are generated for a sample property, power-law fitting is applied, and results (exponent or "non-power-law" flag) are output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for power-law fitting logic (including R2 < 0.9 handling and multi-seed averaging) in `tests/unit/test_scaling_fit.py`
- [ ] T018 [P] [US2] Integration test for learning curve generation on a small subset in `tests/integration/test_learning_curves.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/train_learning_curves.py` to generate **5 training subsets** (sizes: `[1000, 5000, 10000, 20000, 40000]`) per property, training with **1 random seed** per subset using fixed hyperparameters. **Note**: This implementation relies on the amendment ratified in T035 to deviate from the Constitution's 10-subset/3-seed requirement.
- [ ] T020 [US2] Implement `code/fit_scaling_laws.py` to fit $Error = a \cdot N^{-b}$ and classify properties as "non-power-law" if $R^2 < 0.9$. Output `data/processed/scaling_results.csv` with columns: `property_name`, `exponent_b`, `intercept_a`, `r_squared`, `fit_status`.
- [ ] T021 [US2] Implement aggregation logic to produce `data/processed/scaling_results.csv` with exponents and flags
- [ ] T022 [US2] Add error handling for properties with insufficient data points (< 1,000 samples)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

**Goal**: Quantify physical characteristics (spatial locality, symmetry sensitivity), correlate with scaling exponents, and perform statistical validation between property classes.

**Independent Test**: Verify that correlation coefficients, p-values, and class difference significance (p < 0.05) are output correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Pearson correlation and Permutation test logic in `tests/unit/test_statistics.py`
- [ ] T024 [P] [US3] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/analyze_physics.py` to compute "spatial locality" (correlation with valence electron variance) and "symmetry sensitivity" (coefficient of variation)
- [ ] T026 [US3] Implement Pearson correlation analysis between physical metrics and scaling exponents
- [ ] T027 [US3] Implement `code/analyze_physics.py` to perform a **Permutation Test** (primary method for N=2-3 scope) to compare electronic vs. mechanical classes. **Input**: List of scaling exponents per class. **Output**: `p-value` (float). **Note**: This task relies on the amendment ratified in T036 to deviate from the Constitution's Kruskal-Wallis/ANOVA requirement. No fallback logic is implemented as N>=5 is impossible per the Plan.
- [ ] T028 [US3] Implement `code/visualize_results.py` to generate heatmaps and comparative learning curve plots
- [ ] T029 [US3] Generate final summary table with all statistical results in `data/processed/final_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns (Amendments & Validation)

**Purpose**: Improvements that affect multiple user stories and formalize deviations

- [ ] T030 [P] Documentation updates in `docs/` and `README.md`
- [ ] T031 Code cleanup and refactoring for readability
- [ ] T032 Performance optimization (dtype optimization, batch size tuning)
- [ ] T033 [P] Additional unit tests for edge cases (empty datasets, fit failures) in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes critical amendments T035/T036.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `materials_master.parquet`)
- **User Story 3 (P3)**: Depends on US2 completion (requires `scaling_results.csv`)

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
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Unit test for Magpie vector generation in tests/unit/test_descriptors.py"

# Launch all implementation tasks for User Story 1 (sequentially due to data flow):
Task: "Implement code/download_data.py"
Task: "Implement code/generate_descriptors.py"
Task: "Implement data consolidation logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes amendments)
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
 - Developer B: User Story 2 (after US1 data is ready)
 - Developer C: User Story 3 (after US2 data is ready)
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
- **Critical Protocol Note**: Constitution Principle VII (multiple subsets, multiple seeds) is the governing requirement. The Plan's "5x1" note is a feasibility observation that requires a formal amendment (T035) to override. The implementation MUST follow the Constitution unless the amendment is formally recorded and approved.
- **Critical Data Note**: FR-001 requires 15 properties. The implementation MUST validate this count and **halt** if N < 15 (T016).
- **Critical Statistical Note**: Permutation Test is the mandated method for this project's scope (N=2-3). The Kruskal-Wallis test is NOT to be implemented. The amendment (T036) formalizes this change and updates the Spec directly.
- **Execution Order**: T035 and T036 MUST be completed before T019, T020, and T027 to ensure legal compliance before code execution.