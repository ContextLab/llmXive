# Tasks: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Input**: Design documents from `/specs/001-covid-vaccine-signal-detection/`
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

- [ ] T001a Create project directory structure (`code/`, `data/`, `tests/`, `docs/`) per implementation plan
- [ ] T001b Create `requirements.txt` with pinned dependencies: pandas, polars, statsmodels, scipy, matplotlib, requests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 virtual environment and install dependencies from `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup `data/raw/`, `data/processed/`, and `data/outputs/` directory structure with `.gitkeep`
- [ ] T005b [P] Run "Repository-Hygiene Agent's PII scan" as a blocking gate before any data download or commit; generate pass/fail report artifact (Constitution Principle III)
- [ ] T005 [P] Implement `code/ingestion/download.py` skeleton with checksum verification logic; write checksum to `state/...yaml` artifact_hashes map (Constitution Principle III)
- [ ] T006 [P] Create MedDRA hierarchy loader in `code/ingestion/meddra_loader.py` using official mapping
- [ ] T007 [P] Create base data models (VAERS_Report, SOC_Cluster) in `code/analysis/models.py`
- [ ] T008 [P] Configure logging infrastructure in `code/utils/logging_config.py`
- [ ] T009 [P] Create `code/main.py` orchestrator skeleton with argument parsing and basic flow
- [ ] T010 [P] Setup environment configuration management for data paths and random seeds in `code/config.py`
- [ ] T012a [P] Verify source data schema for `vaccination_date` and `onset_date` fields; if missing, document the absence and formally record the waiver of FR-007's 14-30 day window in favor of Calendar-Time Anomaly Detection
- [ ] T012b [P] Generate the "Media Event Flag" dataset (derived from CDC press releases/news) and save to `data/processed/media_event_flag.csv` for use in Bias Adjustment and Temporal Analysis

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, clean, merge, and map VAERS datasets (2020-2023) to create a unified, analysis-ready dataset with SOC mappings.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a small, synthetic subset of VAERS data and verifying that the output CSV contains correctly mapped SOCs, distinct vaccine type flags, and no duplicate or malformed records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for MedDRA mapping logic in `tests/unit/test_meddra_mapping.py`
- [ ] T012 [P] [US1] Unit test for chunked processing memory limits in `tests/unit/test_chunked_processing.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/ingestion/download.py` to fetch VAERS 2020-2023 CSVs from official CDC source (depends on T005 skeleton)
- [ ] T014 [P] [US1] Implement `code/ingestion/preprocess.py` to filter records, handle missing critical fields, and deduplicate (depends on T006 MedDRA loader for validation)
- [ ] T015 [US1] Implement `code/ingestion/merge.py` to join COVID vs. non-COVID data and map MedDRA codes to SOCs using `code/ingestion/meddra_loader.py`
- [ ] T016 [US1] Implement chunked processing logic in `code/ingestion/merge.py` to ensure peak RAM usage remains within acceptable memory constraints.
- [ ] T017 [US1] Add validation logic to ensure `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, and `REPORT_DATE` are present in output
- [ ] T018 [US1] Add logging for ingestion steps, warnings for missing MedDRA codes, and memory usage metrics

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Disproportionality Signal Detection (Priority: P2)

**Goal**: Calculate ROR, PRR, and IC for every SOC, apply Benjamini-Hochberg correction, and identify robust signals based on multi-metric consistency.

**Independent Test**: The analysis can be tested by running the calculation module on a static, pre-computed contingency table and verifying that the output ROR, PRR, and IC values match manual calculations or known benchmarks within an acceptable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for ROR calculation in `tests/unit/test_ror_calculation.py`
- [ ] T020 [P] [US2] Unit test for Benjamini-Hochberg FDR control in `tests/unit/test_fdr_control.py` using synthetic data
- [ ] T021 [P] [US2] Unit test for edge case handling (zero denominator) in `tests/unit/test_edge_cases.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/analysis/disproportionality.py` with ROR, PRR, and IC calculation functions
- [ ] T023 [US2] Implement Benjamini-Hochberg correction logic in `code/analysis/disproportionality.py` for multiple SOC testing
- [ ] T024 [US2] Implement `code/analysis/signal_detection.py` to identify signals where ROR lower 95% CI > 1.0 AND consistency across ≥2 metrics; MUST include the "Bias Adjustment" step by including the "Media Event Flag" (from T012b at `data/processed/media_event_flag.csv`) as a covariate in the calculation to isolate signals from reporting artifacts (depends on T012b)
- [ ] T025 [US2] Implement logic to handle division-by-zero in PRR/IC calculations (return infinity or skip with warning)
- [ ] T026 [US2] Implement validation gate in `code/main.py` (depends on T009) to check SC-001 (≥95% SOCs have valid ROR with non-zero denominator) and exit with error code 1 if failed
- [ ] T027 [US2] Add logging for signal detection steps, FDR control results, and excluded SOCs due to insufficient data

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Temporal Clustering and Visualization (Priority: P3)

**Goal**: Perform calendar-time anomaly detection (Poisson regression) on top signals, compare against non-COVID baseline, and generate forest plots.

**Independent Test**: The visualization module can be tested by feeding it a static set of ROR values and confidence intervals and verifying that the generated PDF/PNG forest plot correctly displays the point estimates and error bars for a representative subset of SOCs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Poisson regression on synthetic weekly counts in `tests/unit/test_temporal.py` (verify that the model identifies the known spike with p < 0.05)
- [ ] T029 [P] [US3] Unit test for forest plot generation in `tests/unit/test_forest_plot.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement control-group comparison using Reports per Million Doses (RPMD) with non-COVID vaccine doses from CDC reports (depends on T009 for data download; URL:; output: `data/processed/rpmd_denominators.csv`)
- [ ] T035 [US3] Implement `code/analysis/temporal.py` with Poisson regression for weekly reporting counts (Calendar-Time Anomaly Detection); MUST load the "Media Event Flag" from `data/processed/media_event_flag.csv` (created in T012b) and include it as a mandatory covariate in the model to control for reporting artifacts (depends on T012b and T030)
- [ ] T031 [US3] Implement `code/visualization/forest_plot.py` to generate forest plots for top candidate signals with 95% CI (depends on T035 results and T030 for context)
- [ ] T032 [US3] Implement logic to handle missing background rates (mark as 'N/A' and proceed with internal baseline)
- [ ] T033 [US3] Add validation to ensure temporal clustering p-values are calculated correctly and reported
- [ ] T034 [US3] Add logging for temporal analysis steps, model convergence, and visualization output paths

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Profile memory usage in `code/ingestion/merge.py` and optimize chunk size
- [ ] T036b [P] Profile memory usage in `code/analysis/disproportionality.py` and optimize data structures
- [ ] T036c [P] Instrument pipeline to log actual peak RAM metric to `state/...yaml` artifact to verify SC-004 (≤7GB)
- [ ] T036d [P] Add explicit instrumentation to log the *actual* peak RAM measurement during the full run to the `state/...yaml` artifact to satisfy SC-004 verification (distinct from profiling in T036a/b)
- [ ] T037 Run end-to-end timing test on `code/main.py` with full dataset to verify runtime ≤ 6 hours
- [ ] T038 [P] Documentation updates in `docs/research.md` detailing methodology and limitations
- [ ] T039 [P] Additional integration tests in `tests/integration/test_pipeline.py` for end-to-end flow
- [ ] T040 [P] Security hardening: Run data sanitization scripts and validate security posture (distinct from PII scan in T005b)
- [ ] T041 Run `quickstart.md` validation to ensure all paths and dependencies are correct

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on signals from US2 and data from US1

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
Task: "Unit test for MedDRA mapping logic in tests/unit/test_meddra_mapping.py"
Task: "Unit test for chunked processing memory limits in tests/unit/test_chunked_processing.py"

# Launch all models for User Story 1 together:
Task: "Create base data models (VAERS_Report, SOC_Cluster) in code/analysis/models.py"
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