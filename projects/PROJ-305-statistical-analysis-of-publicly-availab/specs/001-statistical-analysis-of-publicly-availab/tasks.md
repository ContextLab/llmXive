# Tasks: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Input**: Design documents from `/specs/001-statistical-analysis-covid-vaers/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `output/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scipy, requests, pyarrow, matplotlib, pytest, pytest-cov)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `src/utils/config.py` to define paths, random seeds, and metric thresholds. **Format**: `THRESHOLDS = {"ror_min": 2.0, "ror_ci_min": 1.0, "prr_min": 1.5, "prr_ci_min": 1.0, "ic_min": 0.0, "ic_ci_min": 0.0}`. **Note**: This file defines internal analysis parameters only. It does NOT load external background incidence rates. The analysis methodology (ROR/PRR/IC) uses internal dataset counts as the denominator; external rates are a known limitation and are not calculated.
- [X] T005 [P] Verify the absence of GPU-dependent libraries (e.g., `torch`, `tensorflow`, `cupy`) in `requirements.txt` by running `pip list` and grepping for these packages. **Deliverable**: Log entry "GPU_LIB_CHECK: PASSED" or "GPU_LIB_CHECK: FAILED - <package>" in `logs/gpu_check.log`.
- [ ] T006 [P] Create `contracts/dataset.schema.yaml` defining required columns (`VAX_TYPE`, `SOC_CODE`/`LLT`, `REPT_DATE`, `AGE`)
- [ ] T007 [P] Create `contracts/signal.schema.yaml` defining output structure for signals (ROR, PRR, IC, CI, adjusted_p)
- [ ] T008 Implement `src/data/validate.py` to check raw data against `dataset.schema.yaml` and exit with `E_SCHEMA_MISSING` if failed
- [ ] T009 Implement `src/utils/plots.py` with helpers for generating matplotlib figures (weekly counts, signal tables)
- [ ] T010 Create `src/main.py` as the pipeline orchestrator that enforces phase order and memory checks
- [ ] T039 [US1] Integrate memory check logic into `src/main.py` to halt if RAM usage > 5 GB during data cleaning and enable chunked processing. **Deliverable**: Log message "MEMORY_LIMIT_EXCEEDED: X GB > Y GB" to `logs/memory.log` and exit with code `E_MEMORY_LIMIT`. **Must be completed before T014.**
- [ ] T040 [US2] Integrate memory check logic into `src/main.py` to halt if RAM usage > 7 GB during disproportionality analysis. **Deliverable**: Log message "MEMORY_LIMIT_EXCEEDED: X GB > Y GB" to `logs/memory.log` and exit with code `E_MEMORY_LIMIT`. **Must be completed before T024.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and merge VAERS 2020-2023 datasets, filtering by vaccine type and mapping MedDRA to SOCs.

**Independent Test**: The pipeline runs end-to-end on CPU, outputting a consolidated CSV with valid `VAX_TYPE` ("COVID-19" or "Non-COVID") and non-empty `SOC` fields, with row count > 0.

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for `src/data/download.py` verifying checksum logic in `tests/unit/test_download.py`
- [X] T012 [P] [US1] Unit test for `src/data/validate.py` ensuring `E_SCHEMA_MISSING` is raised on missing columns in `tests/unit/test_validate.py`. **Dependency: T008 must be complete. Status: Pending T008.**
- [X] T013 [P] [US1] Integration test for data pipeline producing valid cleaned CSV in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `src/data/download.py` to fetch VAERS 2020-2023 CSVs from ` or verified mirror, saving to `data/raw/`. **Must use `requests` with explicit error handling; NO synthetic fallbacks allowed.**
- [ ] T015 [US1] Implement `src/data/clean.py` to:
 - Filter records where `VAX_TYPE` contains "COVID-19" (COVID-19 Group).
 - Filter records where `VAX_TYPE` does NOT contain "COVID-19" to define the **Primary Baseline (Non-COVID Group)**: ALL other vaccines reported in the dataset.
 - Create a subset of the Primary Baseline where `VAX_TYPE` contains "Influenza" to define the **Flu-only Group** for sensitivity checks.
 - Create a subset of the Primary Baseline where `VAX_TYPE` does NOT contain "Influenza" to define the **Primary Baseline (Non-COVID, Non-Flu Group)** for the main analysis.
 - Exclude records with missing `SOC` or `REPT_DATE`.
 - Map MedDRA codes to System Organ Classes (SOC) **strictly** using a mapping table loaded from `data/meddra_soc_mapping.csv` (versioned local file). **If the file is missing, the script MUST fail loudly; NO hardcoded fallbacks allowed.**
 - **Implement memory optimization**: Use `pandas.read_csv(chunksize=100000)` and trigger chunked processing if the estimated file size > 5GB OR if runtime RAM monitoring exceeds 5GB.
 - **Output artifacts**: `data/processed/cleaned_vaers.parquet` and `data/processed/cleaned_vaers.csv` containing all groups (COVID-19, Non-COVID, Flu-only, Non-COVID-Non-Flu).
 - **Prerequisite**: T039 must be complete.
- [ ] T018 [US1] Add logging in `src/data/clean.py` to report row counts per group and memory usage stats

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Disproportionality Signal Detection (Priority: P2)

**Goal**: Calculate ROR, PRR, and IC for each SOC, apply Benjamini-Hochberg correction, and identify signals based on 2-out-of-3 metric thresholds.

**Independent Test**: Analysis script produces a table of metrics with finite, non-NaN values for all SOCs with ≥5 reports, and correctly flags signals meeting the 2-out-of-3 rule.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for `src/analysis/disproportionality.py` verifying ROR/PRR/IC calculation logic with continuity correction in `tests/unit/test_disproportionality.py`
- [X] T020 [P] [US2] Unit test for Benjamini-Hochberg correction ensuring monotonic p-values in `tests/unit/test_bh_correction.py`
- [X] T021 [P] [US2] Integration test for signal detection producing `output/signals.csv` in `tests/integration/test_signal_detection.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `src/analysis/disproportionality.py` to generate 2x2 contingency tables for each SOC (Event/No Event vs. COVID-19/Non-COVID, Non-Flu) using the **Primary Baseline (Non-COVID, Non-Flu Group)** as the reference group.
- [X] T023 [P] [US2] Implement continuity correction (add 0.5) in `src/analysis/disproportionality.py` for zero-count cells to prevent division by zero.
- [X] T024 [US2] Implement calculation of ROR, PRR, and IC with 95% confidence intervals in `src/analysis/disproportionality.py` for SOCs with ≥5 total reports.
- [X] T025 [US2] Implement and **apply** the 2-out-of-3 rule (ROR>2.0/CI>1.0, PRR>1.5/CI>1.0, IC>0/CI>0) in `src/analysis/disproportionality.py` to generate the `signal_flag` boolean column for each SOC.
- [ ] T026 [US2] Generate `output/signals.csv` containing all metrics, adjusted p-values, and the `signal_flag` column. **Schema**: `soc`, `ror`, `ror_ci_lower`, `ror_ci_upper`, `prr`, `prr_ci_lower`, `prr_ci_upper`, `ic`, `ic_ci_lower`, `ic_ci_upper`, `p_adj`, `signal_flag`. **Prerequisite**: T025 must be complete. **Prerequisite**: T004 must be complete (to read thresholds).
- [ ] T027 [US2] Implement sensitivity analysis in `src/analysis/sensitivity.py` comparing the **Non-COVID (all other vaccines)** baseline vs **Flu-only** baseline for top 5 signals, explicitly calculating and writing the delta in metrics to `output/sensitivity_analysis.csv`. **Prerequisite**: T026 must be complete.
- [ ] T028 [US2] Generate `output/sensitivity_analysis.csv` containing delta metrics for top 5 signals. **Schema**: `soc`, `ror_delta`, `prr_delta`, `ic_delta`, `baseline_type`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Descriptive Temporal Profile (Priority: P3)

**Goal**: Generate weekly reporting profiles for top 5 candidate SOCs relative to median report date, acknowledging data limitations.

**Independent Test**: Script generates time-series plots for top SOCs labeled as "Reporting Time" and correctly applies Benjamini-Hochberg correction to cross-sectional metrics.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for `src/analysis/temporal.py` verifying weekly aggregation logic in `tests/unit/test_temporal.py`
- [X] T031 [P] [US3] Integration test for temporal profile generation producing plots in `tests/integration/test_temporal_profiles.py`

### Implementation for User Story 3

- [ ] T032 [US3] Identify top 5 candidate SOCs from `output/signals.csv`. **Edge Case**: If fewer than 5 signals meet the threshold, select all available signals. If zero, generate a placeholder file `output/temporal_profiles/empty_signal_warning.txt`. **Dependency**: T026 must be complete.
- [ ] T033 [US3] Implement weekly aggregation in `src/analysis/temporal.py` relative to the group median `REPT_DATE` (not vaccination date) and generate the specific weekly count plot files (PNG) for the top-ranked SOCs.
- [ ] T034 [US3] Implement plotting logic in `src/analysis/temporal.py` to generate figures labeled "Reporting Time" (explicitly noting lack of `VACCINATION_DATE` data).
- [ ] T035 [US3] Generate `output/temporal_profiles/` directory containing weekly count plots for top 5 SOCs (or placeholder if <5 signals).
- [ ] T037 [US3] Add disclaimer in `output/report.md` that temporal analysis is descriptive and does not establish causality. **MUST explicitly state: "Analysis is labeled 'Reporting Time' due to lack of vaccination date data."**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Priority: P1)

**Goal**: Validate statistical correctness, memory constraints, and generate the final report.

**Independent Test**: All success criteria (SC-001 to SC-004) are verified and logged.

- [ ] T051 [P] Implement memory profiling in `src/main.py` to track peak RAM usage using `tracemalloc` or `psutil` during pipeline execution.
- [ ] T052 [P] Generate `output/memory_profile.json` containing the peak memory usage (in GB) and a pass/fail status against the 7 GB constraint. **Prerequisite**: T051 must be complete.
- [ ] T053 [P] Verify Benjamini-Hochberg monotonicity on the *actual* generated `output/signals.csv` (SC-002). **Deliverable**: Log entry "BH_MONOTONICITY: PASSED" or "FAILED" to `output/validation.log`. **Prerequisite**: T026 must be complete.
- [ ] T054 [P] Calculate the proportion of SOCs with valid ROR, PRR, and IC calculations (SC-001). **Deliverable**: Log the proportion (e.g., "VALID_SOC_PROPORTION: 0.98") to `output/validation.log`. **Prerequisite**: T026 must be complete.
- [ ] T055 [P] Generate `output/report.md` compiling all metrics, temporal profiles, sensitivity analysis, and limitations. **Requirements**:
 - Read peak memory usage from `output/memory_profile.json` and include it in the report.
 - Verify the string "Reporting Time" appears in the temporal section header and the limitation section.
 - Include the 'Reporting Propensity' vs 'Absolute Risk' disclaimer.
 - Include the limitation that background incidence rates are not calculated.
 - **Prerequisite**: T052, T053, T054, T035 must be complete.
- [ ] T056 [P] Run final validation script to ensure all required output files exist and are non-empty. **Dependency**: T053 must be complete (check `output/validation.log` for BH monotonicity).

**Checkpoint**: Final validation complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in `README.md` and `docs/`
- [ ] T047 Code cleanup and refactoring
- [ ] T049 [P] Additional unit tests for edge cases (zero counts) in `tests/unit/`
- [ ] T050 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation & Reporting (Phase 6)**: Depends on all user stories
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output AND Phase 2 (Foundational) for config and memory checks.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 signal identification

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for src/data/download.py in tests/unit/test_download.py"
Task: "Unit test for src/data/validate.py in tests/unit/test_validate.py"
Task: "Integration test for data pipeline in tests/integration/test_pipeline.py"

# Launch all data processing tasks together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/clean.py (filtering and mapping)"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Disproportionality Analysis)
 - Developer C: User Story 3 (Temporal Analysis)
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
- **Critical**: Ensure all data processing tasks respect the available RAM constraints and use chunked processing where necessary.
- **Critical**: Ensure all statistical calculations handle zero counts via continuity correction.
- **Critical**: Ensure temporal analysis is explicitly labeled as "Reporting Time" and not "Post-Vaccination Time".
- **Critical**: SC-005 is marked [deferred] in the spec; no implementation is required for the proportion of signals satisfying the 2-out-of-3 rule beyond the initial validation in T025.
- **Critical**: Data loaders must FAIL LOUDLY if real data fetch fails; synthetic fallbacks are strictly prohibited.
- **Critical**: Background rates are NOT calculated; the analysis uses internal dataset counts. Any mention of external rates must be framed as a limitation, not a calculated metric.
- **Critical**: T016 has been removed to eliminate redundancy; all filtering logic is now in T015.
- **Critical**: T012 is pending T008 implementation.
- **Critical**: T024b has been removed as the 'Background Rate Unknown' flagging is inconsistent with the ROR/PRR/IC methodology which uses internal counts.
- **Critical**: Phase 4 (User Story 2) explicitly depends on Phase 2 (Foundational) to ensure T004 (config) and T039/T040 (memory checks) are complete before signal calculation.