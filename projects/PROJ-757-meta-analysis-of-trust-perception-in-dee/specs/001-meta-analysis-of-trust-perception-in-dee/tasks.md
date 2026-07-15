# Tasks: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

**Input**: Design documents from `/specs/001-meta-analysis-trust-deepfake/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 Create project structure per `plan.md` (`code/`, `data/`, `results/`, `tests/`)
- [ ] T002 Initialize Python 3.10 project with `requirements.txt` (including `requests`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `rpy2`, `pypdf`, `pdfplumber`)
- [ ] T003 [P] Initialize R 4.3+ environment and create `renv.lock` for `metafor` and `esc` packages <!-- ATOMIZE: requested -->
- [ ] T004 [P] Configure `pytest` and create `tests/unit/` and `tests/integration/` directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create `data/search_results/`, `data/screening/`, `data/harmonized/`, and `results/` directories
- [X] T006 [P] Implement `code/utils.py` with logging, config loading, checksum generation logic, AND a utility function to parse `data/screening/inclusion_criteria.yaml`. **Note**: This task depends on T017 completing first; do not execute T006 until T017 has generated the YAML file. <!-- FAILED: unspecified -->
- [~] T008 Implement mock API response fixtures for OpenAlex, Semantic Scholar, and arXiv in `tests/unit/`
- [~] T009 Implement synthetic data generator for effect size math verification in `tests/unit/`
- [ ] T017 [P] Generate `data/screening/inclusion_criteria.yaml` programmatically. The YAML MUST contain keys for exclusion codes: `NO_TRUST_METRIC`, `NO_CONTROL_CONDITION`, `NO_MODERATOR_DATA`, and `NOT_PEER_REVIEWED`, mapping to the specific logic defined in `plan.md` Phase 1.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Literature Search and Study Screening (Priority: P1) 🎯 MVP

**Goal**: Execute automated searches, export raw data, and perform dual-reviewer screening with Kappa calculation.

**Independent Test**: Can be fully tested by running the search script against mock API responses and verifying the output CSV contains correct fields and screening logic flags correct exclusion reasons.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for search query construction and API backoff logic in `tests/unit/test_search.py`
- [X] T011 [P] [US1] Unit test for screening logic (exclusion codes: NO_TRUST_METRIC, NO_CONTROL_CONDITION, NO_MODERATOR_DATA) in `tests/unit/test_screening.py`
- [X] T012 [P] [US1] Unit test for Cohen's Kappa calculation and adjudication flagging in `tests/unit/test_screening.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/01_search_and_screen.py` to query OpenAlex, Semantic Scholar, and arXiv with `"deepfake" AND "trust"` and `"AI‑generated face" AND "trustworthiness"` queries <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 3, column 1:
 **Task ID**: T013
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 3, column 2:
 **Task ID**: T013
 ^) -->
- [ ] T014 [US1] Implement export of raw results to `data/search_results/raw_studies.csv` with fields: title, year, source, abstract, DOI
- [ ] T015 [US1] Implement dual-reviewer simulation logic in `code/01_search_and_screen.py` applying `data/screening/inclusion_criteria.yaml`
- [ ] T016 [US1] Implement Cohen's Kappa calculation; if Kappa < 0.6, log exactly "Human Adjudication Required (Kappa < 0.6)", generate `data/screening/adjudication_request.csv` listing disputed studies, and exit with code 1 (HALT) to wait for human input.
- [ ] T016.5 [US1] **Adjudication Workflow**: Implement logic to detect the `adjudication_request.csv` flag. If present, the system must pause and wait for a human operator to manually edit `screening_log.csv` (resolving disputes) and clear the flag. Upon detection of resolved flags, re-run the screening logic (T015) and proceed to T018.
- [ ] T018 [US1] **Deferred**: Removed. PRISMA generation moved to Phase N (T042) to ensure it uses final harmonized data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Effect Size Calculation and Data Harmonization (Priority: P2)

**Goal**: Extract statistics, convert to Cohen's d/log-odds, and handle missing SDs with strict imputation/exclusion rules as per FR-003.

**Independent Test**: Can be fully tested by providing synthetic study statistics and verifying effect size calculation precision (tolerance set to a sufficiently small threshold) and correct flagging of reconstructed/missing SDs.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for Cohen's d calculation from means/SDs in `tests/unit/test_effect_size.py`
- [ ] T020 [P] [US2] Unit test for log-odds conversion from odds ratio and CI in `tests/unit/test_effect_size.py`
- [ ] T021 [P] [US2] Unit test for SD reconstruction logic (exact t/p vs rounded p) and imputation logic in `tests/unit/test_effect_size.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/02_effect_size_calc.py` to parse means, SDs, t-stats, p-values from `data/screening/screening_log.csv`
- [ ] T023 [US2] Implement logic to preserve raw p-value strings in `p_value_raw` field
- [ ] T024 [US2] Implement strict SD handling per FR-003 and Plan Phase 2:
 - **Case A (SD Present)**: Use directly. Set `included_in_primary=True`.
 - **Case B (SD Missing, Exact t/p)**: Reconstruct SD. Set `sd_reconstructed=True`. **Set `included_in_primary=False`** (Exclude from primary pool).
 - **Case C (SD Missing, Rounded p-value e.g., "p < 0.05")**: **Set `included_in_primary=False`** (Exclude from primary pool). Do NOT impute.
 - **Case D (SD Missing, Unrecoverable)**: **Set `included_in_primary=False`** (Exclude from primary pool). Do NOT impute for primary pool.
 - **Sensitivity Analysis Only**: For Case B, C, and D, calculate a "sensitivity effect size" using the mean SD of similar studies (n ± 10) and store in a separate `sensitivity_effect_size` column, but ensure the primary `effect_size` column remains empty or flagged for exclusion in the primary pool.
 - **CRITICAL**: All studies are retained in the output dataset for downstream sensitivity analysis, but only those with `included_in_primary=True` are used for the main meta-analysis.
- [ ] T025 [US2] Implement conversion to Cohen's d (or log-odds) with high decimal precision.
- [ ] T026 [US2] Export full harmonized dataset to `data/harmonized/effect_sizes.csv` with flags (`sd_imputed`, `sd_reconstructed`, `included_in_primary`) ensuring all studies are present, not just the primary pool
- [ ] T027 [US2] Implement aggregation logic for multiple effect sizes per study (select highest reliability)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Meta-Analysis and Moderator Modeling (Priority: P3)

**Goal**: Fit random-effects models, run meta-regressions, and generate robustness checks.

**Independent Test**: Can be fully tested on a small synthetic dataset with known heterogeneity and moderator effects.

### Tests for User Story 3

- [ ] T028 [P] [US3] Integration test for `metafor` invocation via `rpy2` with synthetic data in `tests/integration/test_meta_analysis.py`
- [ ] T029 [P] [US3] Unit test for sensitivity analysis (leave-one-out) logic in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/03_meta_analysis_driver.py` to invoke `code/03_meta_analysis.R` via `rpy2`
- [ ] T031 [US3] Create `code/03_meta_analysis.R` script using `metafor` to fit random-effects model on `included_in_primary=True` studies ONLY
- [ ] T032 [US3] Implement logic to check study count (k < 10); if low, switch to Subgroup Meta-Analysis or report "Insufficient Power"
- [ ] T033 [US3] Implement meta-regression in R for moderators "realism" and "media-literacy" (excluding studies lacking moderator data)
- [ ] T034 [US3] Implement leave-one-out sensitivity analysis and Egger's test for publication bias in R
- [ ] T035 [US3] Implement sensitivity analysis excluding all `sd_reconstructed=True` studies from the primary pool to verify robustness
- [ ] T036 [US3] Implement sensitivity analysis with "Conservative Variance Inflation" (replace missing SDs with max observed SD)
- [ ] T037 [US3] Generate `results/analysis_output.csv` with pooled effect, CI, p-value, I², Q-stat
- [ ] T038 [US3] Generate `results/robustness/sensitivity_analysis.csv`
- [ ] T039 [US3] Generate `results/figures/Forest.pdf` using `matplotlib`/`seaborn` with explicit `plt.xlabel`, `plt.ylabel`, and `plt.errorbar` (visible caps) to ensure labeled axes and visible CIs
- [ ] T040 [US3] Generate `results/figures/Funnel.pdf` using `matplotlib`/`seaborn` with explicit `plt.xlabel`, `plt.ylabel`, and visible CI lines

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] [US3] Validate that `Forest.pdf` and `Funnel.pdf` contain labeled axes and visible CIs. Use `pypdf` or `pdfplumber` to programmatically verify: 1) Presence of text objects matching expected axis labels (e.g., "Standardized Mean Difference"), and 2) Presence of path objects with stroke attributes (non-zero width, non-white color) representing confidence intervals. Fail build if these specific path/text objects are missing.
- [ ] T042 [P] [US3] Generate `results/figures/PRISMA_flow.pdf`. **Input**: Derive counts programmatically from `data/harmonized/effect_sizes.csv` (post-harmonization) and `data/screening/screening_log.csv`. The diagram MUST reflect the final included studies after all exclusion steps (screening + harmonization).
- [ ] T043 [P] Run `pytest` for all unit and integration tests
- [ ] T044 [P] Verify reproducibility by re-running pipeline and checking `state/checksums.txt`
- [ ] T045 [P] Update `README.md` with execution instructions and expected outputs
- [ ] T046 [P] Validate `quickstart.md` (if generated) against the implemented pipeline

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T006** must run after **T017**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`screening_log.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`effect_sizes.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - **Except T006 which waits for T017**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for search query construction and API backoff logic in tests/unit/test_search.py"
Task: "Unit test for screening logic (exclusion codes) in tests/unit/test_screening.py"
Task: "Unit test for Cohen's Kappa calculation in tests/unit/test_screening.py"

# Launch implementation for User Story 1:
Task: "Implement code/01_search_and_screen.py to query APIs"
Task: "Implement export of raw results to data/search_results/raw_studies.csv"
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
 - Developer A: User Story 1 (Search/Screen)
 - Developer B: User Story 2 (Effect Sizes)
 - Developer C: User Story 3 (Meta-Analysis)
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
- **Critical Constraint**: All meta-analysis tasks in Phase 5 MUST run on CPU-only environment; `metafor` via `rpy2` is CPU-tractable. Do not use GPU-specific libraries.
- **Data Integrity**: No synthetic data is used for final analysis; only real data from API searches and real statistical calculations.
- **FR-003 Compliance**: Task T024 explicitly implements the exclusion logic for missing SDs and rounded p-values, ensuring they are NOT included in the primary pool.
- **Sensitivity Analysis**: Task T026 ensures all studies are retained for T035 sensitivity checks.
- **Visual Validation**: Task T041 uses `pypdf`/`pdfplumber` for programmatic verification of specific PDF elements (text/path objects).
- **PRISMA Timing**: Task T042 generates the PRISMA diagram only after all data harmonization is complete, ensuring accuracy.