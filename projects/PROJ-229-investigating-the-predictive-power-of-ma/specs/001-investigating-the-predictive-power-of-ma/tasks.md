# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Input**: Design documents from `/specs/001-phase-change-predictive-power/`
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
  - Delivered as a MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: Create directories `code/data`, `code/models`, `code/utils`, `tests/unit`, `tests/integration`, `data/raw`, `data/processed`, `data/results`, and `specs/001-phase-change-predictive-power/contracts`.
- [ ] T002 Initialize Python 3.11 project with `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml` dependencies
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `config.yaml` for API keys, random seeds, and time/memory constraints
- [ ] T005 [P] Implement basic logging infrastructure and error handling in `code/utils/`
- [ ] T006 [P] Create data directory structure (`data/raw`, `data/processed`, `data/results`)
- [ ] T007 Create base schema definitions in `specs/001-phase-change-predictive-power/contracts/` (dataset.schema.yaml, model_output.schema.yaml)
- [ ] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring
- [ ] T013 [P] [US1] Implement `code/data/load_external_validation.py` to fetch or load the 50 literature PCMs (DOI: 10.1016/j.matt.2024.01.001) for later validation. Must handle mapping to Materials Project IDs.
- [ ] T013b [US1] Implement fallback logic in `code/data/load_external_validation.py` (or separate module) to handle failure case: if the NIST overlap (training data proxy validation) is < 500 compounds, switch target to `melting_point` and flag the limitation as per Spec US-1 Acceptance Scenario 3. This task must execute AFTER T011/T012 produce the training data proxy validation stats.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve a curated subset of Materials Project data, compute elemental/structural descriptors, and prepare a clean dataset for modeling within 7GB RAM.

**Independent Test**: Execute the data retrieval script and verify that the output CSV contains at least 5,000 compounds with non-null values for melting point, latent heat (where available), and computed feature columns, fitting within 7 GB RAM.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T010 [US1] Integration test for data pipeline in `tests/integration/test_pipeline.py`. **Must run after T015** to ensure full pipeline implementation is complete.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data/fetch_materials_project.py` to query Materials Project API for compounds with melting points and heat capacity, handling rate limits and fallback strategies. Output must include training data proxy validation stats (NIST overlap count).
- [ ] T012 [US1] Implement `code/data/compute_descriptors.py` to generate:
  - Elemental descriptors (atomic number, electronegativity, radius)
  - Crystal graph representations using `pymatgen`'s `StructureGraph` module
  - Ensure output fits within 7GB RAM and handles missing structures via imputation or exclusion
- [ ] T014 [US1] Implement `code/utils/collinearity_utils.py` for Variance Inflation Factor (VIF) analysis to detect definitional dependencies (e.g., atomic radius vs ionic radius). **Must run after T012**.
- [ ] T015 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (fetch -> feature engineering -> VIF check -> save processed CSV).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train Random Forest, Gradient Boosting, SHAP-analyzed trees, and PySR symbolic regression models on CPU within the 6-hour window, ensuring R² > 0.0.

**Independent Test**: Run the training pipeline and verify that models achieve R² > 0.0 on the validation set and that symbolic regression terminates within 4 hours on the free-tier runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/models/train_baselines.py` to train Random Forest and Gradient Boosting models with fixed random seeds and memory constraints
- [ ] T018 [US2] Implement SHAP analysis in `code/models/train_baselines.py` (or separate module) to generate ranked feature importances without GPU
- [ ] T019 [US2] Implement `code/models/train_symbolic.py` using PySR with:
  - Strict time budget (hours)
  - Regularized feature set (post-VIF)
  - Logic to output at least one explicit mathematical formula
- [ ] T020 [US2] Implement `code/models/evaluate.py` to compute R² scores, perform paired t-tests between baselines and interpretable models (SC-002), and log performance metrics
- [ ] T021 [US2] Add logic to `code/models/evaluate.py` to flag limitations if PySR fails to converge (r < 0.0) and default to SHAP results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate derived rules against external literature PCMs, perform sensitivity analysis on thresholds, and finalize associational framing.

**Independent Test**: Apply derived rules to an external set of literature PCMs and verify performance drop ≤ 10% compared to test set; generate sensitivity analysis report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Integration test for validation pipeline in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T023 [US3] Implement external validation logic in `code/models/evaluate.py`:
  - Load literature PCMs (from T013/T013b)
  - Apply derived symbolic rules or feature rankings
  - **Determine N dynamically** via Phase 0 research findings (do not hard-code 10) for the top-N highest-value PCMs.
  - Calculate ranking accuracy on the **top N** PCMs (resolving SC-003)
  - Adjust target metric based on Phase 0 feasibility (latent heat vs melting point)
  - Verify success criterion: ≥ 60% accuracy on top N (SC-003)
- [ ] T024 [US3] Implement sensitivity analysis in `code/utils/stability_checks.py` to sweep feature importance thresholds over a **continuous range of small magnitudes (e.g., 0.0 to 0.2 in steps of 0.01)** and report false-positive/negative rates (FR-004, SC-004).
- [ ] T025 [US3] Add final collinearity diagnostic in `code/utils/collinearity_utils.py` to flag any remaining definitional dependencies and adjust interpretation to descriptive/associational (FR-006)
- [ ] T026a [US3] Generate correlation analysis report section in `research.md` summarizing SC-001 (Pearson correlation between structural features and phase-change suitability). **Explicitly calculate and publish the measured Pearson coefficient and the specific threshold value derived from the research phase**, replacing any '[deferred]' placeholders.
- [ ] T026b [US3] Generate model comparison report section in `research.md` summarizing SC-002 (R² comparison results and t-test). **Insert measured values from previous steps**.
- [ ] T026c [US3] Generate final report in `research.md` and `paper/` drafts that explicitly includes:
  - Generalization accuracy on literature set (SC-003)
  - Sensitivity analysis results (SC-004)
  - **Explicit associational framing** (FR-007) stating findings are correlational, not causal. **Must include the exact text of the 'Critical Methodological Note' from the Plan** to ensure strict framing.
  - **Insert measured values from previous steps**, replacing any '[deferred]' placeholders.
- [ ] T027 [US3] Run reproducibility check: Execute full pipeline end-to-end on a fresh runner to verify checksums and artifact hashes (Phase 3, Step 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. **Dependencies**: Depends on completion of US1, US2, and US3.

- [ ] T028 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T029 Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T030 [P] Additional unit tests for descriptor computation and stability checks in `tests/unit/`
- [ ] T031 Run `quickstart.md` validation to ensure all steps are reproducible

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (processed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (models/rules) and US1 output (external validation data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (or data scripts before model scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel IF data dependencies are managed (US2 and US3 depend on US1 output)
- All tests for a user story marked [P] can run in parallel
- Different utility modules (VIF, stability) can be developed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data quality, memory usage)
5. Proceed to US2 only if US1 succeeds

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate data pipeline
3. Add User Story 2 → Test independently → Validate model training within time limits
4. Add User Story 3 → Test independently → Validate external generalization
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data pipeline)
   - Developer B: User Story 2 (Model training) - can start once US1 data is available
   - Developer C: User Story 3 (Validation) - can start once US2 models are available
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
- **CRITICAL**: All tasks must run on CPU-only free-tier CI (a limited number of cores, limited RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **CRITICAL**: Use real data sources only (Materials Project API, NIST, literature DOIs). No synthetic/fake data generation.
- **CRITICAL**: Do not hard-code empirical values (like top-N counts or sweep ranges) unless explicitly derived from research or defined in the spec.