# Tasks: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001a Verify root project directory structure defined in `plan.md` exists at `projects/PROJ-160-investigating-the-impact-of-early-life-s/`; create if missing.
- [X] T001b [P] Create subdirectories `code/`, `data/raw/`, `data/processed/`, `tests/`, `contracts/` INSIDE the `projects/PROJ-160-investigating-the-impact-of-early-life-s/` directory created in T001a
- [X] T002a [P] Create `projects/PROJ-160-investigating-the-impact-of-early-life-s/requirements.txt` with dependencies: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `joblib`, `pytest`
- [ ] T002b [P] Install dependencies from `projects/PROJ-160-investigating-the-impact-of-early-life-s/requirements.txt` in an isolated virtualenv at `.venv`; verify success by running `python -m pip list` and confirming all packages are present. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with paths, random seeds (line 12), and constants for ABCD Release 4.0
- [X] T005 [P] Implement data loading utilities in `code/data/loaders.py` (handling CSV/TSV parsing)
- [ ] T006a [P] Create `contracts/dataset.schema.yaml` defining the schema for the preprocessed dataset (columns: ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV, Normalized_Volumes)
- [ ] T006b [P] Create `contracts/model_results.schema.yaml` defining the schema for model outputs (β, CI, p-value, corrected_p-value)
- [ ] T007 Create base entity definitions in `code/analysis/results.py` (AnalysisResult, StatisticalModel)
- [ ] T008 Configure error handling and logging infrastructure in `code/main.py`: Implement try/except blocks for all I/O operations; log errors to `logs/pipeline.log` in JSON format; raise custom exceptions on failure.
- [~] T009 Setup environment configuration management (`.env` support if needed, though paths are relative)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire ABCD Study Release 4.0 data, filter for quality/completeness, and normalize volumes.

**Independent Test**: Verify pipeline downloads CSVs, filters missing ACE/poor MRI quality, and outputs normalized dataset with ≥80% retention.

### Implementation for User Story 1

- [~] T014 [US1] Implement `code/data/acquisition.py` to download ABCD phenotypic and subcorticalSegmentationStats files from official portal, verify MD5 checksums (FR-001) <!-- FAILED: unspecified -->
- [~] T015 [US1] Implement `code/data/preprocessing.py` to exclude participants with missing ACE scores or poor MRI quality flags (FR-002)
- [~] T016 [US1] [Depends on T015] Implement `code/data/preprocessing.py` to normalize CA3, DG, subiculum volumes by dividing by ICV, storing with ≥4 decimal precision (FR-003) <!-- SKIPPED: non-mapping output -->
- [~] T017 [US1] [Depends on T016] Implement `code/data/preprocessing.py` to check ACE score skewness and apply **log-transformation** if |skewness| > 1.0 (FR-011).
- [~] T018 [US1] [Depends on T017] Implement `code/data/preprocessing.py` to handle extreme ACE outliers (>3 SD) by flagging them (appending a flag column to `data/processed/cleaned_dataset.csv`) for downstream sensitivity analysis, without auto-exclusion (Edge Case). This flagging supports sensitivity analysis and does not alter the FR-002 exclusion logic.
- [~] T019 [US1] Generate `data/processed/cleaned_dataset.csv` with all required columns (ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV, Normalized_Volumes)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py`
- [~] T011 [P] [US1] Integration test for download and filter logic in `tests/integration/test_acquisition.py`
- [~] T012 [P] [US1] Unit test for ICV normalization precision in `tests/unit/test_preprocessing.py`
- [~] T013 [P] [US1] Unit test for log-transformation logic in `tests/unit/test_preprocessing.py` <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 1, column 1:
 class TestMRIDetection:
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 2, column 13:
 """Tests for MRI QC column detecti...
 ^) -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Fit linear mixed-effects models for CA3, DG, subiculum and CA3:DG ratio, apply Bonferroni correction.

**Independent Test**: Verify three separate models output standardized β, 95% CI, p-values (corrected and uncorrected) and complete within 45 mins.

### Implementation for User Story 2

- [~] T024 [US2] Implement `code/analysis/modeling.py` to fit LMM with formula `subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)` for CA3, DG, subiculum (FR-004)
- [~] T025 [US2] Implement `code/analysis/modeling.py` to calculate VIF for covariates; if VIF > 5, apply residualization strategy (regress ACE on collinear covariate) before fitting (Edge Case: Multicollinearity)
- [~] T026 [US2] Implement `code/analysis/results.py` to extract β coefficients, 95% CIs, and uncorrected p-values from model summaries
- [~] T027 [US2] Implement `code/analysis/results.py` to apply Bonferroni correction (threshold) and report corrected p-values (FR-005)
- [~] T028 [US2] Implement `code/analysis/modeling.py` to compute CA3:DG volume ratio and fit exploratory model with same covariates (FR-006)
- [~] T029 [US2] Ensure all output reports explicitly frame findings as **ASSOCIATIONAL** only (FR-010)
- [~] T030 [US2] Save results to `data/processed/model_results.json` and `data/processed/model_results_summary.csv`

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Contract test for model results schema in `tests/contract/test_model_results.py`
- [~] T021 [P] [US2] Integration test for LMM fitting and formula validation in `tests/integration/test_modeling.py`
- [~] T022 [P] [US2] Unit test for Bonferroni correction logic (p < 0.0167) in `tests/unit/test_results.py`
- [~] T023 [P] [US2] Unit test for CA3:DG ratio calculation in `tests/unit/test_modeling.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform cluster-level permutation tests and sensitivity analyses to validate findings.

**Independent Test**: Verify 5,000 permutation tests complete within 3 hours, sensitivity sweeps run, and ICV-restricted analysis outputs effect size change.

### Implementation for User Story 3

- [~] T035 [US3] Implement `code/analysis/robustness.py` to perform **non-parametric permutation tests** (5,000 permutations) to verify linear model assumptions per Constitution Principle VI and Spec FR-007. This task implements the authorized cluster-level permutation (permuting family_id) required for LMM robustness in clustered data, ensuring the method aligns with the requirement to verify linear model assumptions without violating statistical validity. (FR-007)
- [~] T036 [US3] Implement `code/analysis/robustness.py` to parallelize permutations using `joblib` with `n_jobs=2` to meet 3-hour runtime constraint (SC-003, Edge Case: Timeout)
- [~] T037 [US3] Implement `code/analysis/robustness.py` to generate a sensitivity analysis summary table in `data/processed/sensitivity_report.csv`. The table must list counts of significant findings for thresholds read from `code/config.py` (default: `{0.01, 0.05, 0.1}` to allow configurability per FR-008) AND calculate the variation metric (standard deviation of counts) to quantify dependency (SC-005). (FR-008, FR-009, SC-005)
- [~] T038 [US3] Implement `code/analysis/robustness.py` to subset data for ICV within 1 SD of mean and re-run primary analysis to calculate % change in effect size (FR-009)
- [~] T039 [US3] Aggregate all robustness metrics (parametric vs permutation p-values, threshold sensitivity, effect stability) into `data/processed/robustness_report.json`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T031 [P] [US3] Contract test for robustness output schema in `tests/contract/test_robustness_schema.py`
- [~] T032 [P] [US3] Integration test for cluster-level permutation logic in `tests/integration/test_robustness.py`
- [~] T033 [P] [US3] Unit test for alpha sweep logic in `tests/unit/test_robustness.py`
- [~] T034 [P] [US3] Unit test for ICV restriction subsetting logic in `tests/unit/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T040a [P] Update `README.md` with installation instructions and usage examples
- [~] T040b [P] Update `specs/001-gene-regulation/quickstart.md` with project overview and data requirements
- [~] T041 Code cleanup and refactoring in `code/analysis/` and `code/data/`: Remove unused imports, enforce line length < 88, add docstrings to all public functions.
- [ ] T042 Performance optimization: Ensure data loading streams only necessary columns to fit in GB RAM (Plan: Computational Feasibility)
- [ ] T043 [P] Run full test suite `pytest` and verify all contract tests pass
- [ ] T044 Run `quickstart.md` validation if generated
- [ ] T045 Verify total pipeline runtime (Acquisition → Robustness) is ≤ 6 hours (SC-006)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data acquisition/preprocessing before modeling
- Modeling before robustness checks
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Integration test for download and filter logic in tests/integration/test_acquisition.py"
Task: "Unit test for ICV normalization precision in tests/unit/test_preprocessing.py"
Task: "Unit test for log-transformation logic in tests/unit/test_preprocessing.py"

# Launch all implementation for User Story 1 together:
Task: "Implement code/data/acquisition.py..."
Task: "Implement code/data/preprocessing.py..."
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Robustness)
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions (limited CPU, constrained RAM, no GPU). No 8-bit quantization or large model training.