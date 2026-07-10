# Tasks: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Input**: Design documents from `/specs/001-predict-yield-strength-bcc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project directories: `code/`, `data/`, `data/raw/`, `data/intermediate/`, `data/processed/`, `data/provenance/`, `data/results/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 [P] Create `code/requirements.txt` with pinned versions for `pandas`, `scikit-learn`, `requests`, `numpy`, `shap`, `pyyaml`, `mp-api`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`
- [ ] T004 [P] Setup Git hooks for pre-commit checks (seeds, imports)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/config.py` with paths, seeds (42), and API key handling
- [X] T006 Implement `code/utils/logging.py` with structured logging for provenance
- [X] T007 Implement `code/utils/checksums.py` to generate SHA-256 for `data/` artifacts
- [~] T008 Create `contracts/` schema files: `dataset.schema.yaml`, `output.schema.yaml`
- [~] T009 Implement `code/main.py` orchestration skeleton with error handling for `ERR_INSUFFICIENT_DATA`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Validation (Priority: P1) 🎯 MVP

**Goal**: Merge experimental yield strength data (MatNavi/NIST) with DFT elastic constants (Materials Project API) into a validated dataset with ≥20 rows.

**Independent Test**: Execute `code/ingestion/` pipeline; verify `data/intermediate/merged.csv` has ≥20 rows with non-null `yield_strength_MPa` and `shear_modulus_GPa`. If <20, system halts with `ERR_INSUFFICIENT_DATA`. Verify `data/provenance/dft_queries.jsonl` contains query logs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for BCC filtering logic in `tests/unit/test_filter_bcc.py`
- [~] T011 [P] [US1] Integration test for API retry/backoff logic in `tests/integration/test_api_retry.py`
- [~] T012 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_merged_schema.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/ingestion/fetch_experimental.py` to download BCC Fe-alloy data from the URL defined in `code/config.py` (e.g., `CONFIG.EXPERIMENTAL_DATA_URL`)
- [~] T014 [US1] Implement `code/ingestion/fetch_dft.py` to query Materials Project API for elastic constants (with exponential backoff)
- [~] T015 [US1] Implement `code/ingestion/merge_and_filter.py` to join datasets, filter for Space Group 229 (BCC), and handle nulls
- [~] T016 [US1] Implement `code/ingestion/merge_and_filter.py` to handle range values (e.g., "200-250") by taking midpoints and flagging uncertainty
- [~] T017 [US1] Write the final merged dataset to `data/intermediate/merged.csv` and verify row count ≥ 20; raise `ERR_INSUFFICIENT_DATA` if not
- [~] T018 [US1] Add logging for API queries and failures to `data/provenance/dft_queries.jsonl`
- [~] T019 [US1] Generate `data/provenance/checksums.txt` for all raw and intermediate files
- [~] T020 [US1] Update `state/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml` with artifact hashes

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Baseline Comparison (Priority: P2)

**Goal**: Train Random Forest with DFT features vs. composition-only baseline, perform k-fold cross-validation, and calculate statistical significance (p-value, power).

**Independent Test**: Run `code/modeling/train.py` and `code/modeling/evaluate.py`; verify `data/results/output.json` contains R², MAE (both models), p-value (from paired t-test), statistical power, and Pearson correlation (SC-001).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Unit test for feature encoding (one-hot, fractions) in `tests/unit/test_features.py`
- [~] T022 [P] [US2] Unit test for statistical power calculation in `tests/unit/test_power_analysis.py`
- [~] T023 [P] [US2] Integration test for nested CV loop in `tests/integration/test_cv_loop.py`

### Implementation for User Story 2

- [~] T024 [US2] Implement `code/modeling/features.py` to encode composition (one-hot, atomic fractions) and normalize DFT descriptors
- [~] T025 [US2] Implement `code/modeling/features.py` to calculate Variance Inflation Factors (VIF) and report multicollinearity
- [~] T026 [US2] Implement `code/modeling/train.py` to train Random Forest with k-fold CV (composition-only baseline)
- [~] T027 [US2] Implement `code/modeling/train.py` to train Random Forest with composition + DFT descriptors
- [~] T028 [US2] Implement `code/modeling/evaluate.py` to calculate R² and MAE for both models
- [~] T029 [US2] Implement `code/modeling/evaluate.py` to perform **paired t-test** on fold-wise errors and calculate p-value (per spec FR-005/SC-003; overrides plan.md's Wilcoxon mention)
- [~] T030 [US2] Implement `code/modeling/evaluate.py` to calculate statistical power (1 - beta) based on the t-test effect size and report if < 0.8 (FR-009/SC-008)
- [ ] T031 [US2] Calculate and report Pearson correlation between Shear Modulus and Yield Strength (SC-001, FR-005) using `data/intermediate/merged.csv` as input and write to `output.json`
- [ ] T032 [US2] Write final metrics to `data/results/output.json` conforming to `contracts/output.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate TreeSHAP values, permutation importance, and bootstrap stability analysis to validate model robustness.

**Independent Test**: Run `code/interpretability/`; verify `data/results/output.json` contains top 5 features, SHAP summary, std_dev from sample-size sweep (FR-007), and std_dev from fixed-sample bootstrap (FR-008) with `is_stable` boolean.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for TreeSHAP calculation on small dataset in `tests/unit/test_shap.py`
- [ ] T034 [P] [US3] Unit test for bootstrap resampling logic in `tests/unit/test_bootstrap.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement `code/interpretability/shap_analysis.py` to calculate TreeSHAP values for the DFT-enhanced model
- [ ] T036 [US3] Implement `code/interpretability/shap_analysis.py` to generate permutation importance rankings (highlighting DFT descriptors)
- [ ] T037 [US3] Implement `code/interpretability/bootstrap_stability.py` to run **Bootstrap Stability analysis by re-sampling the REAL dataset** with a **sample-size sweep (n=10 to n=50)** and calculate standard deviation of feature importance across the sweep (FR-007/SC-004)
- [ ] T038 [US3] Implement `code/interpretability/bootstrap_stability.py` to calculate standard deviation of feature importance across **10 bootstrapped samples** of the full dataset (FR-008/SC-005)
- [ ] T039 [US3] Implement logic to check if std_dev of key DFT descriptors < 0.05 across the 10 bootstrapped samples (from T038) and report `is_stable` boolean (FR-008/SC-005)
- [ ] T040 [US3] Generate plots (SHAP summary, stability distribution) and save to `data/results/`
- [ ] T041 [US3] Update `data/results/output.json` with all Success Criteria: SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update `README.md` with installation instructions, usage examples, and data sources
- [ ] T043 [P] Update `docs/api.md` with function signatures for `code/ingestion/`, `code/modeling/`, and `code/interpretability/`
- [ ] T044 Code cleanup and refactoring for readability
- [ ] T045 Profile pipeline execution and optimize memory/CPU usage to ensure < 6h runtime on 2 CPU cores
- [ ] T046 [P] Run full pipeline end-to-end integration test
- [ ] T047 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 model

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
Task: "Contract test for merged dataset schema in tests/contract/test_merged_schema.py"
Task: "Integration test for API retry/backoff logic in tests/integration/test_api_retry.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_experimental.py"
Task: "Implement fetch_dft.py"
Task: "Implement merge_and_filter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥20 rows, no synthetic data)
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Interpretability)
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
- **CRITICAL**: No synthetic data allowed. If real data < 20 rows, system MUST halt.
- **CRITICAL**: All DFT data must come from Materials Project API (Constitution Principle VII).
- **CRITICAL**: Statistical tests must be exactly as specified (paired t-test, sample-size sweep, fixed-sample bootstrap).
- **NOTE**: Task T029 implements the **paired t-test** per spec FR-005, overriding the plan.md's mention of Wilcoxon. The plan.md should be updated to match the spec in a future revision.