# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-037-investigating-the-correlation-between-gu/`, `data/raw/`, `data/processed/`, `data/outputs/`, `code/`, `tests/`, `docs/`
- [ ] T001b [P] Create empty `README.md`, `.gitignore`, and `requirements.txt` placeholder files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002a [P] Create `requirements.txt` at `projects/PROJ-037-investigating-the-correlation-between-gu/` with dependencies: `pandas`, `scikit-learn`, `scipy`, `statsmodels`, `biom-format`, `skbio`, `numpy`, `matplotlib`, `seaborn`, `requests`, `biopython`. **Note**: Do NOT use `american-gut` package; use `biom-format` and `skbio` with manual download scripts as defined in plan.md.
- [ ] T002b [P] Create virtual environment (`python -m venv venv`) and install requirements in `code/` context <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `setup.cfg` or `pyproject.toml`
- [ ] T004 [P] Create `code/__init__.py` and utility modules for configuration and logging in `code/utils/`
- [~] T006a [P] Define data validation schema in `code/schemas.py` matching `contracts/dataset.schema.yaml` (specify column types: participant_id=str, shannon=float, etc.)
- [X] T006b [P] Implement validation logic in `code/utils/validators.py` to check non-null constraints and data types for the merged cohort
- [X] T007 [P] Setup random seed management for reproducibility in `code/utils/seeding.py`
- [ ] T008 [P] Create base configuration loader for environment variables in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Definition (Priority: P1) 🎯 MVP

**Goal**: Download, merge, and filter American Gut Project and Open Humans data to produce a clean, analysis-ready dataset.

**Independent Test**: The pipeline runs in isolation to verify that it outputs a single CSV/TSV file where row counts match the intersection of valid microbiome and sleep records, and all required columns are present and non-null.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for data merging logic in `tests/test_ingestion.py` (verify N calculation)
- [X] T010 [P] [US1] Unit test for missing data imputation logic in `tests/test_ingestion.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/ingestion.py` to download American Gut Project 16S rRNA data (using `biom-format` and `skbio` for parsing; manual download via `requests` or `wget` from canonical URLs) and Open Humans sleep metadata; verify data integrity via checksums
- [X] T012 [US1] Implement merge logic in `code/ingestion.py` to join datasets on Participant ID; if no matches found (N=0), log a WARNING "No matching participants found; proceeding with available sample size" to `logs/ingestion.log` and continue execution (do NOT exit with code 1)
- [X] T013 [US1] Implement filtering logic in `code/ingestion.py` to exclude participants with missing sleep/microbiome data
- [X] T014 [US1] Implement outlier capping for sleep duration (<2h or >16h) at 1st/99th percentiles in `code/ingestion.py`
- [X] T015 [US1] Implement covariate imputation (median/mode) for BMI, age, antibiotic history in `code/ingestion.py`
- [X] T016 [US1] Generate summary report in `code/ingestion.py` listing the **exact retained participant count (N)** and distribution of key covariates (age, BMI, antibiotic use)
- [ ] T017 [US1] Save final merged cohort to `data/processed/cohort_merged.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Associational Analysis and Visualization (Priority: P2)

**Goal**: Compute diversity metrics, perform FDR-corrected correlation tests, dbRDA, and generate visualizations.

**Independent Test**: The analysis module executes on the cleaned dataset to produce a results table of correlation coefficients and p-values, along with static image files of the required plots.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for alpha diversity calculation in `tests/test_analysis.py`
- [X] T019 [P] [US2] Unit test for FDR correction logic in `tests/test_analysis.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/diversity.py` to calculate Alpha diversity (Shannon, Simpson) and Beta diversity (Bray-Curtis) per participant
- [X] T021 [US2] Implement `code/analysis.py` to perform Spearman/Pearson correlation tests between diversity metrics and sleep variables (duration, quality, chronotype)
- [X] T022 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis.py` for all p-values
- [X] T023 [US2] Implement distance-based redundancy analysis (dbRDA) in `code/analysis.py` for non-linear screening of sleep vs. beta diversity
- [X] T024 [US2] Implement Generalized Linear Model (GLM) in `code/analysis.py` adjusting for confounders (age, BMI, diet type, medication, antibiotic history); **Note**: Explicitly flag that "diet timing" (required by FR-004) is unavailable in AGP and "diet type" is used as a substitute per plan mitigation; document this requirement deviation in the output report.
- [X] T025 [US2] Implement PERMANOVA in `code/analysis.py` strictly for categorical sleep variables (not continuous); use dbRDA for continuous variables as per plan mitigation.
- [~] T026 [US2] Generate heatmap of taxa-sleep associations in `code/viz.py` and save to `data/outputs/heatmap.png`
- [~] T027 [US2] Generate PCoA ordination plot colored by sleep quality scores in `code/viz.py` and save to `data/outputs/pcoa_sleep_quality.png`
- [ ] T028 [US2] Generate final results table in `data/outputs/correlation_results.csv` including effect sizes, p-values, and FDR-corrected p-values
- [ ] T029 [US2] Implement logic in `code/report.py` to ensure the **entire report** (headers, captions, text) explicitly frames all findings as "associational" and avoids causal language, verifying FR-008 compliance.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Validate stability via bootstrap resampling and perform sensitivity analysis on significance thresholds.

**Independent Test**: The validation script produces a secondary set of results on bootstrap resamples and a sensitivity report showing how results change when the significance threshold is varied.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for bootstrap resampling logic in `tests/test_validation.py`
- [X] T031 [P] [US3] Unit test for sensitivity sweep logic in `tests/test_validation.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement bootstrap resampling (1000 iterations) in `code/validation.py` to estimate 95% confidence intervals for top 5 correlations; **Note**: Explicitly implement logic where confidence intervals including zero are treated as valid negative results (correcting the spec's SC-002 flaw), and report these as such.
- [ ] T033 [US3] Implement logic in `code/validation.py` to skip resampling if N < 40; write status to `data/outputs/validation_status.json` with field `resampling_skipped: true` and reason "Insufficient sample size"
- [ ] T034 [US3] Implement sensitivity analysis in `code/validation.py` sweeping significance threshold over the specific set of values: `[0.01, 0.05, 0.1]` as defined in spec SC-003.
- [ ] T035 [US3] Generate sensitivity report in `data/outputs/sensitivity_report.csv` showing variation in significant taxa counts
- [ ] T036 [US3] Update `code/report.py` to include a section detailing bootstrap stability (CIs) and sensitivity sweep results, explicitly framing all findings as associational

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` and `README.md`
- [ ] T044 Code cleanup and refactoring
- [ ] T045 Performance optimization across all stories (ensure < 6h runtime on N=200)
- [ ] T046 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T047 Security hardening (data handling)
- [ ] T048 Run `quickstart.md` validation

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data merging logic in tests/test_ingestion.py"
Task: "Unit test for missing data imputation logic in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py to download AGP and Open Humans data"
Task: "Implement merge logic in code/ingestion.py"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Associational Analysis)
 - Developer C: User Story 3 (Validation)
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
- **CRITICAL**: Adhere to CPU-only constraints (no GPU, no 8-bit models). All statistical tests must run on multi-core systems with sufficient memory resources.
- **CRITICAL**: Ensure all data sources are real and reachable; no synthetic data fabrication.
- **CRITICAL**: All findings must be framed as associational; no causal claims.
- **CRITICAL**: Removed Phase 6 (Molecular Mechanism) as it was out of scope and computationally infeasible for the specified environment.