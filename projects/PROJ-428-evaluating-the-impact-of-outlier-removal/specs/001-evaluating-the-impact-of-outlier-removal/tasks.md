# Tasks: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

**Input**: Design documents from `/specs/001-evaluating-outlier-removal-impact/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-428-evaluating-the-impact-of-outlier-removal/`) <!-- FAILED: unspecified -->
- [X] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, linearmodels)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/src/__init__.py` and global random seed configuration (`random.seed(42)`)
- [ ] T005 [P] Implement data directory structure: `data/raw/`, `data/processed/`, `data/results/`, `state/` (ensure atomic creation using `mkdir -p`)
- [X] T006 Create base schema validation utilities in `code/src/validators.py` using PyYAML to validate against `contracts/*.schema.yaml`
- [~] T007 [P] Implement checkpoint/restart mechanism in `code/src/checkpoint.py` including logic to ENFORCE 100 Monte Carlo replicates as per Constitution Principle VI; if the runner limit is exceeded, the system MUST fail the run and log a critical error (NO fallback to 50 replicates)
- [~] T008 Configure logging infrastructure in `code/src/logger.py` with file and console handlers
- [~] T011 [US1] Download 5 public datasets from the UCI Machine Learning Repository to `data/raw/uci_*.csv`, identify univariate continuous variables, and output 5 clean CSV files with baseline variance values to `data/processed/uci_clean_*.csv` (Per Spec FR-001 and US-1 Acceptance 1; depends on T006 for schema validation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Contaminated Dataset and Compute Baseline Metrics (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic clean distributions, simulate outlier contamination at varying rates, and compute baseline variance estimates to establish ground truth.

**Independent Test**: Execute data generation script and verify output files contain expected rows and variance calculations match manual checks on a small subset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for `Dataset` and `ContaminationProfile` schemas in `code/tests/test_contracts.py`
- [~] T010 [P] [US1] Unit test for synthetic data generation (Normal, LogNormal) in `code/tests/test_data_generator.py`

### Implementation for User Story 1

- [~] T011b [US1] Generate synthetic clean distributions (Normal, LogNormal, Exponential, Beta, Gamma) with known variance parameters (generated randomly within defined ranges), saving data to `data/raw/synthetic_clean_*.csv` and ground truth parameters to `state/synthetic_params.json`
- [~] T012 [P] [US1] Implement synthetic data generation logic (Normal, LogNormal, Exponential, Beta, Gamma) with known variance in `code/src/data_generator.py` (Output: `data/raw/synthetic_clean_*.csv`, `state/synthetic_params.json`)
- [ ] T013 [US1] Implement outlier injection logic (Cauchy/extreme scaling) at varying contamination rates, saving contaminated data to `data/processed/contaminated_*.csv` and injection profile to `data/processed/injection_profile.json`
- [ ] T014 [US1] Implement baseline variance calculation using the synthetic clean data (from T012) and save results to `data/results/baseline_metrics.json`
- [ ] T015 [US1] Add logging for dataset downloads, injection rates, and variance calculations in `code/src/data_generator.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Outlier Removal Strategies and Calculate Bias/MSE (Priority: P2)

**Goal**: Apply IQR filtering, Winsorization, and Trimmed Variance to contaminated datasets and calculate bias and MSE against ground truth.

**Independent Test**: Run removal pipeline on a single simulated dataset and verify output contains three distinct variance estimates and finite bias/MSE values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for `RemovalMethod` and `EstimationResult` schemas in `code/tests/test_contracts.py`
- [ ] T017 [P] [US2] Unit test for IQR filtering (1.5× rule) in `code/tests/test_outlier_removal.py`
- [ ] T018 [P] [US2] Unit test for Winsorization (5th/95th percentiles) in `code/tests/test_outlier_removal.py`
- [ ] T019 [P] [US2] Unit test for Trimmed Variance logic in `code/tests/test_outlier_removal.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement IQR filtering method (standard interquartile range rule) in `code/src/outlier_removal.py`
- [ ] T021 [P] [US2] Implement Winsorization method (lower and upper percentiles) in `code/src/outlier_removal.py`
- [ ] T022 [P] [US2] Implement Trimmed Variance method loading trim percentage from `config.yaml` (default 0.1 if missing) in `code/src/outlier_removal.py`
- [ ] T023 [US2] Implement `metrics.py` to calculate Bias and MSE against known ground truth in `code/src/metrics.py`
- [ ] T024 [US2] Execute IQR filtering on contaminated data and calculate Bias/MSE, saving results to `data/results/iqr_results.json`
- [ ] T025 [US2] Execute Winsorization on contaminated data and calculate Bias/MSE, saving results to `data/results/winsorization_results.json`
- [ ] T026 [US2] Execute Trimmed Variance on contaminated data and calculate Bias/MSE, saving results to `data/results/trimmed_results.json`
- [ ] T027 [US2] Add logging for removed row counts and metric calculations in `code/src/outlier_removal.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison and Generate Visualizations (Priority: P3)

**Goal**: Run multiple Monte Carlo replicates per condition, perform Repeated Measures ANOVA with Bonferroni correction, and generate interaction plots.

**Independent Test**: Run analysis script on aggregated results and verify output includes statistical summary table with p-values and interaction plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Contract test for aggregated results schema in `code/tests/test_contracts.py`
- [ ] T034 [P] [US3] Unit test for ANOVA and Bonferroni correction logic in `code/tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement Monte Carlo loop (100 replicates) integrating outputs from T024, T025, T026 and T007, saving aggregated results to `data/results/monte_carlo_replicates.csv` and checkpoints to `state/checkpoint.json` (Depends on completion of T024-T027)
- [ ] T029a [P] Update `plan.md` Summary section to replace "Linear Mixed-Effects Models (LMM)" with "Repeated Measures ANOVA (or Friedman test)" to align with Spec FR-006 (Prerequisite for T029)
- [ ] T029 [US3] Implement Repeated Measures ANOVA (or Friedman test) with Bonferroni correction in `code/src/analysis.py`
- [ ] T030 [US3] Generate interaction plots (MSE vs Contamination, faceted by Distribution, lines by Method) saving files `mse_vs_contamination.png` and `method_comparison_faceted.png` to `data/results/figures/`
- [ ] T031 [US3] Save statistical summary table and plots to `data/results/statistical_analysis.csv` and `data/results/figures/` in `code/src/analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring for CPU efficiency
- [ ] T037 Performance optimization to ensure completion within 6 hours on 2 CPU cores
- [ ] T038 [P] Additional unit tests for edge cases (zero IQR, no continuous variables) in `code/tests/`
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
- **User Story 2 (P2)**: Depends on T014 (Baseline metrics) - Requires contaminated data from US1
- **User Story 3 (P3)**: Depends on T024/T025/T026 (Removal results) - Requires aggregated results from US2

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
Task: "Contract test for Dataset and ContaminationProfile schemas in code/tests/test_contracts.py"
Task: "Unit test for synthetic data generation in code/tests/test_data_generator.py"

# Launch all implementation for User Story 1 together:
Task: "Generate synthetic ground truth data in code/src/data_generator.py"
Task: "Implement outlier injection logic in code/src/data_generator.py"
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
- **Constitutional Note**: Per Principle VI, a sufficient number of Monte Carlo replicates are NON-NEGOTIABLE. Tasks that propose reducing this count are invalid.