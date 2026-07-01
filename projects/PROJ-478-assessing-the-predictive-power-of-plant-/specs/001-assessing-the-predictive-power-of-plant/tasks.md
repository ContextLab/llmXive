# Tasks: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

**Input**: Design documents from `/specs/feat-assess-plant-traits/`
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

- [ ] T001a [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/src`
- [ ] T001b [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/src/data`
- [ ] T001c [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/src/modeling`
- [ ] T001d [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/src/analysis`
- [ ] T001e [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/src/utils`
- [ ] T001f [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/tests`
- [ ] T001g [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/data/raw`
- [ ] T001h [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/data/processed`
- [ ] T001i [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/data/metadata`
- [ ] T001j [P] Create directory `projects/PROJ-478-assessing-the-predictive-power-of-plant-/code/results`
- [ ] T001k [P] Create `__init__.py` in all `src/` and `tests/` subdirectories
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, geopandas, rasterio, statsmodels, requests, tqdm, numpy, pandas)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `src/utils/config.py` for constants, seeds, and paths
- [ ] T006 [P] Implement `src/utils/logging.py` for structured logging and progress bars
- [ ] T007 Create base data models (Pydantic/Dataclasses) for `Species`, `OccurrenceRecord`, `ClimateRasterStack`, `TraitProfile` in `src/models/`
- [ ] T008 Setup environment configuration management (`.env` handling for API keys)
- [ ] T009 Implement checksum verification utilities in `src/utils/checksum.py` for raw data integrity
- [ ] T009b [P] Implement URL reachability and checksum verification gate in `src/utils/verify_data.py` to validate GBIF, WorldClim, and TRY URLs before download (Constitution Principle II)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate a climate‑only SDM for a single species (Priority: P1) 🎯 MVP

**Goal**: Establish baseline SDM performance using climate-only variables for a single species (e.g., *Helianthus annuus*) to serve as a reference point.

**Independent Test**: Run the workflow for one species and verify that a cleaned occurrence file, climate rasters, and cross-validated AUC/TSS values are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for spatial thinning logic in `tests/unit/test_preprocess.py` (verify ≥80% retention)
- [ ] T011 [P] [US1] Integration test for end-to-end climate-only training in `tests/integration/test_us1_climate_only.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data/fetch_gbif.py` to retrieve occurrences, remove duplicates, and apply spatial thinning (a default distance, min 1km) per FR-001. **Logic**: If thinning reduces records to <80% of raw, iteratively reduce thinning distance by 1km steps until retention >= 80% or 1km minimum is reached. If still insufficient, flag species as 'insufficient data'.
- [ ] T013 [US1] Implement `src/data/fetch_climate.py` to download WorldClim bioclimatic layers and align to occurrence extent per FR-002
- [ ] T014 [US1] Implement `src/data/preprocess.py` for density-based background sampling (a sufficiently large set of points) and coordinate alignment
- [ ] T015 [US1] Implement `src/modeling/train_rf.py` for CPU-only Random Forest training (n_estimators=100, max_depth=10) with k-fold CV
- [ ] T016 [US1] Implement `src/modeling/metrics.py` to calculate AUC and TSS scores
- [ ] T017 [US1] Create `src/main.py` entry point to orchestrate the single-species climate-only pipeline
- [ ] T018 [US1] Add error handling for "No occurrence records" and "Model training failure" (retry with reduced max_depth) per Edge Cases

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Add functional trait covariates and re‑train the SDM (Priority: P2)

**Goal**: Augment the climate model with functional traits using a Leave-One-Species-Out (LOSO) design with **known trait values** for the held-out species.

**Independent Test**: Run the workflow for a subset of species and validate the model against the held-out species using the known trait values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for trait source verification (Handbook 2013) in `tests/unit/test_fetch_traits.py`
- [ ] T020 [P] [US2] Integration test for LOSO loop with known traits in `tests/integration/test_us2_loso_known_traits.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/data/fetch_traits.py` to retrieve SLA, seed mass, height from TRY, verify source metadata (FR-010). **Logic**: If source is not 'Handbook 2013', flag the value as 'unverified protocol' but **retain** the record with a warning. If any of the three required traits are missing entirely (null/NaN), flag the species as '[missing trait]'.
- [ ] T022 [US2] Implement `src/modeling/loso_cv.py` to orchestrate the LOSO cycle: train on N-1 species, then for the held-out species, use its **known trait values** (from T021) as inputs to the 'climate+traits' model. Train and evaluate using these known traits. **Note**: This strictly follows Spec FR-004 and US-2. **Priority**: The Spec's requirement for 'known trait values' takes precedence over the Plan's 'Trait Imputation' design decision. Do NOT implement trait imputation.
- [ ] T023 [US2] Implement `src/modeling/collinearity.py` to compute Variance Inflation Factor (VIF) for the full predictor set and flag VIF > 5 (FR-011)
- [ ] T024 [US2] Extend `src/main.py` to run the full LOSO loop for all species with complete trait data
- [ ] T025 [US2] Implement logic to exclude species with **missing** traits (not unverified) from the trait-augmented branch and log exclusions (FR-006). **Logic**: Only exclude if any of the three required traits are null/NaN. 'Unverified protocol' traits must be retained.
- [ ] T026b [US2] Add logging to track "unverified protocol" traits and include a warning in the final report (do NOT exclude these species from the analysis)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Conduct a comparative statistical analysis across 50 species (Priority: P3)

**Goal**: Evaluate community-level performance differences between climate-only and trait-augmented models using paired t-tests and sensitivity analysis.

**Independent Test**: Execute the full pipeline for all focal species, run paired t-tests with Bonferroni correction, and verify sensitivity analysis results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for paired t-test and Bonferroni correction logic in `tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_us3_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `src/analysis/stats.py` to perform paired two-sided t-tests on AUC/TSS results, apply Bonferroni correction (FR-005, FR-008), and calculate Cohen's d. **Output**: `results/stats_report.json` with corrected p-value and effect size. **Primary Method**: Spec FR-005 t-test. **Note**: This task implements the Spec's required verification. The Plan's LMM suggestion is optional (see T029b).
- [ ] T029b [US3] Implement optional exploratory Linear Mixed-Effects Modeling (LMM) in `src/analysis/stats.py` to account for non-independence. **Note**: This is optional and does not replace the primary t-test in T029 for acceptance criteria.
- [ ] T030 [US3] Implement sensitivity analysis sweep over thresholds {0.01, 0.02, 0.05} to verify direction of improvement in ≥67% of cases (FR-009, US-3). **Output**: `results/sensitivity_analysis.json` containing a table with columns: `threshold`, `count_positive_delta`, `percentage_positive`.
- [ ] T031 [US3] Implement logic to check mean AUC < 0.70 and flag in report (SC-002)
- [ ] T031b [US3] Perform power analysis to determine the exact N required (targeting a sufficient sample size if feasible) and report the final count (resolving scope ambiguity)
- [ ] T032 [US3] Generate `results/model_results.json` with per-species metrics and `results/stats_report.json` with aggregate test results
- [ ] T033 [US3] Add explicit disclaimer to final report framing results as associative, not causal (FR-007)
- [ ] T034 [US3] Create final report generator that includes VIF warnings, p-values, effect sizes, and sensitivity tables

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T035 [P] Documentation updates in `README.md` and `docs/` with execution instructions
- [ ] T036 Code cleanup and refactoring of `src/` modules. **Rules**: Remove unused imports, enforce black formatting, reduce cyclomatic complexity < 10.
- [ ] T037 Performance optimization to ensure total runtime ≤ 6 hours on CPU-only runner
- [ ] T038 [P] Run quickstart.md validation script
- [ ] T039 Verify all data provenance logs in `data/metadata/` match spec requirements
- [ ] T040 Final integration test: Run full pipeline from raw data fetch to final report generation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data structures (Species, OccurrenceRecord)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2

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
Task: "Unit test for spatial thinning logic in tests/unit/test_preprocess.py"
Task: "Integration test for end-to-end climate-only training in tests/integration/test_us1_climate_only.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_gbif.py"
Task: "Implement fetch_climate.py"
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions runners (limited cores, constrained RAM). No GPU, no CUDA, no 8-bit quantization.
- **Data Integrity**: All datasets must be real and fetched from verified URLs (GBIF, WorldClim, TRY). No synthetic data generation for inputs.
- **Validation Design**: The LOSO loop MUST use the held-out species' **known trait values** (from TRY) for the 'climate+traits' model, as per Spec FR-004 and US-2. Do NOT use trait imputation. **Note**: This Spec requirement overrides the Plan.md's "Critical Design Decision" if they conflict.
- **Statistical Method**: The primary verification method is the Spec-mandated paired t-test with Bonferroni correction (T029). LMM (T029b) is optional exploratory analysis.