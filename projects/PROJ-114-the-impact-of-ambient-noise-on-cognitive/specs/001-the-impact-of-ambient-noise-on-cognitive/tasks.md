# Tasks: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

**Input**: Design documents from `/specs/001-ambient-noise-cognitive-flexibility/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scipy, statsmodels, scikit-learn, pyyaml, jsonschema, pytest)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T019 [P] Implement power analysis justification: Generate `docs/power_analysis_report.md` containing calculated effect size, alpha, power, and N=150 justification (FR-008); verify report contains N=150 and specific statistical parameters. **Note: This task must be completed BEFORE any synthetic data generation or data collection logic.**
- [ ] T043 [P] Validate calibration simulation logic: Define reference tone parameters in `code/config.py` and implement validation script in `code/scripts/validate_calibration.py` to ensure simulation fidelity matches real-world expectations (FR-009); generate `data/processed/calibration_validation_report.json`.
- [ ] T004 [P] Define JSON Schema contracts in `contracts/dataset.schema.yaml` for Participant, NoiseLog, and TaskPerformance (Input entities only)
- [~] T005 [P] Implement `code/scripts/update_state.py` to compute SHA-256 hashes of artifacts and update `state/projects/PROJ-114-.../current_stage.yaml`
- [~] T006 [P] Setup logging infrastructure and environment configuration management in `code/config.py`
- [ ] T007 Create base data classes/entities in `code/models.py` matching Key Entities in spec.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Implement the data ingestion, calibration, and validation pipeline to generate a clean dataset from raw logs.

**Independent Test**: A script can load synthetic JSONL logs, apply calibration checks, bin noise data, exclude invalid participants, and output a processed CSV without errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for calibration logic (error margin >2dB exclusion) in `tests/unit/test_data_ingestion.py`
- [ ] T011 [P] [US1] Unit test for 1-minute bin gap analysis in `tests/unit/test_data_ingestion.py`
- [ ] T012 [P] [US1] Integration test for full ingestion pipeline with synthetic data in `tests/integration/test_ingestion_pipeline.py`

### Implementation for User Story 1

- [ ] T018 [US1] [P] Create `code/scripts/generate_synthetic_data.py` to produce deterministic synthetic logs and task metrics for pipeline validation (NOT for hypothesis testing); ensure data includes edge cases (0dB, gaps >20%).
- [ ] T013 [US1] Implement `code/data_ingestion.py` to load raw JSONL/CSV from `data/raw/` and validate against `contracts/dataset.schema.yaml`
- [ ] T014 [US1] Implement device-specific calibration protocol simulation in `code/data_ingestion.py` (FR-009): flag participants if `error_margin > 2dB` or `calibration_status` missing
- [ ] T015 [US1] Implement gap analysis logic in `code/data_ingestion.py` (FR-007): bin noise logs into 1-minute intervals, calculate `valid_logging_proportion`, exclude participants with <80% valid hours [UNRESOLVED-CLAIM: c_2d334f2e — status=not_enough_info] OR **detect and flag any single continuous gap >20% of total session time [UNRESOLVED-CLAIM: c_6b03692e — status=not_enough_info] **; generate exclusion log.
- [ ] T016 [US1] Implement outlier removal and edge case handling in `code/data_ingestion.py`: remove reaction times >3 SD from mean [UNRESOLVED-CLAIM: c_11c863ae — status=not_enough_info]; **handle 0dB as 'Low' noise [UNRESOLVED-CLAIM: c_630605c4 — status=not_enough_info]**; **flag participants with >90% silent sessions for model singularity check [UNRESOLVED-CLAIM: c_7645dfdc — status=not_enough_info]**; generate `data/processed/outlier_audit_log.json` containing counts and IDs of removed rows for audit.
- [ ] T044 [US1] Implement Error Count Validation/Cleaning in `code/data_ingestion.py`: handle missing error counts, impute or flag as appropriate, and ensure clean error data before CFI calculation; generate `data/processed/cleaned_error_counts.csv`.
- [ ] T017 [US1] [Depends on: T016, T044] Implement CFI calculation in `code/data_ingestion.py` (FR-002): compute z-scored RT difference and z-scored error count; apply logic: if r > 0.7 use RT diff only, else sum them; output `data/processed/cfi_metrics.csv` with columns [participant_id, cfi_score]; verify file exists.
- [ ] T040 [US1] Implement Valid Data Proportion Report generation: Aggregate pass/fail rates against N=150 target (SC-001) and generate `data/processed/valid_data_proportion_report.json` containing proportion of valid participants and recruitment status.
- [ ] T020 [US1] Create `docs/quickstart.md` with instructions to run synthetic data generation and ingestion pipeline; verify file contains a runnable command block for `python code/scripts/generate_synthetic_data.py` and expected output path.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Engine (Priority: P2)

**Goal**: Fit the linear mixed-effects model with quadratic terms and perform post-hoc analysis.

**Independent Test**: A fixed dataset of simulated participants yields a model summary with fixed effects, p-values, and likelihood-ratio test results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_model_fitting.py`
- [ ] T022 [P] [US2] Unit test for Likelihood-Ratio Test logic in `tests/unit/test_model_fitting.py`
- [ ] T023 [P] [US2] Integration test for full model fitting with synthetic data in `tests/integration/test_model_pipeline.py`

### Implementation for User Story 2

- [ ] T041 [US2] [P] Define JSON Schema contract for `ModelResult` in `contracts/dataset.schema.yaml` (Output entity); **must be completed before T030**.
- [ ] T042 [US2] [P] Generate descriptive statistics table: Aggregate continuous logs into three discrete categories (Low: <45dB, Moderate: 45-65dB, High: >65dB) [UNRESOLVED-CLAIM: c_7ab46834 — status=not_enough_info] as per FR-001; calculate counts, means, and standard deviations for each category; output `data/processed/descriptive_noise_categories.csv` and summary report.
- [ ] T024 [US2] Implement collinearity diagnostic in `code/model_fitting.py`: compute VIF for `noise_level` and `noise_variability`; if VIF > 5, apply residualized variability approach [UNRESOLVED-CLAIM: c_a53a076f — status=not_enough_info]
- [ ] T025 [US2] Implement LMM fitting in `code/model_fitting.py` (FR-003): fixed effects (continuous noise, quadratic noise, residualized variability), random intercept (participant ID), dependent variable (CFI)
- [ ] T026 [US2] Implement Likelihood-Ratio Test in `code/model_fitting.py` (FR-004): compare quadratic model vs. linear baseline [UNRESOLVED-CLAIM: c_d474805c — status=not_enough_info]
- [ ] T027 [US2] Implement post-hoc Tukey HSD test in `code/model_fitting.py` (FR-006) for noise categories (Low, Moderate, High)
- [ ] T028 [US2] Implement family-wise error rate (FWER) calculation in `code/model_fitting.py` (SC-004) and explicitly compare against nominal alpha; generate verification report
- [ ] T029 [US2] Handle model convergence failures in `code/model_fitting.py`: fallback to simpler linear model or report diagnostic error
- [ ] T030 [US2] [Depends on: T041] Serialize model results to `data/models/model_result.json` including coefficients, p-values, CIs, and convergence status; verify JSON contains keys [coefficients, p_values, ci_lower, ci_upper, convergence_status] and matches schema in `contracts/dataset.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Validate findings via threshold sweeps and sensitivity checks to ensure the "sweet spot" hypothesis is robust.

**Independent Test**: Running the sensitivity script with modified thresholds produces a stability report showing variation in effect sizes and significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity_analysis.py`
- [ ] T032 [P] [US3] Integration test for sensitivity analysis with synthetic data in `tests/integration/test_sensitivity_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement threshold sweep logic in `code/sensitivity_analysis.py` (FR-005): re-run model with varying thresholds.
- [ ] T034 [US3] Implement robustness check in `code/sensitivity_analysis.py`: exclude high-sensitivity participants and re-fit model.
- [ ] T035 [US3] Generate stability report in `code/sensitivity_analysis.py` (SC-003): compare effect sizes and significance across sweeps; report false-positive rate variation; **explicitly calculate and report the specific stability metric (e.g., coefficient variance) for the Moderate noise category effect size**.
- [ ] T036 [US3] Aggregate results into `data/models/sensitivity_report.json`; verify JSON contains keys [threshold_sets, effect_sizes, significance_flags, false_positive_rates, moderate_category_stability].

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization

**Purpose**: Generate final documentation and update project state

- [ ] T037 Generate `docs/paper_draft.md` from model results and sensitivity reports; populate with model coefficients from `data/models/model_result.json` and sensitivity data from `data/models/sensitivity_report.json`; verify file contains sections [Methods, Results, Discussion] and cites specific p-values.
- [ ] T038 [P] Run `code/scripts/update_state.py` to hash all artifacts and update `state/`.
- [ ] T039 [P] Execute end-to-end pipeline validation on GitHub Actions runner (NFR-001: <6 hours, <6GB RAM [UNRESOLVED-CLAIM: c_5b710f06 — status=not_enough_info]).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T019 (Power Analysis) and T043 (Calibration Validation) must run first in this phase.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data cleaning from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2

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
Task: "Unit test for calibration logic in tests/unit/test_data_ingestion.py"
Task: "Unit test for 1-minute bin gap analysis in tests/unit/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Create base data classes/entities in code/models.py"
Task: "Implement `code/data_ingestion.py` to load raw JSONL/CSV"
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
- **Real Data Constraint**: Synthetic data is ONLY for pipeline validation. Real data must be sourced from a valid URL or package for the final hypothesis test (US2).
- **CPU Constraint**: All statistical methods must run on a standard multi-core CPU configuration with sufficient memory for typical workloads, without requiring GPU acceleration. No low-precision models or heavy deep learning.