# Tasks: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

**Input**: Design documents from `/specs/001-assessing-mond-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T003a [P] Initialize `pyproject.toml` or `ruff.toml` with linting configuration (ruff/flake8)
- [X] T003b [P] Initialize `.black` or `pyproject.toml` formatting configuration (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T048 [P] Generate `contracts/dataset.schema.yaml` defining the schema for parsed galaxy data (FR-002, FR-003)
- [ ] T049 [P] Generate `contracts/fit_results.schema.yaml` defining the schema for model fit outputs (FR-007, FR-009)
- [X] T050 [US1/2/3] Implement data schema validators in `tests/contract/test_schemas.py` matching the generated contracts. **Dependency**: T048 AND T049 must complete first. (Depends on T048 AND T049 completion - removed [P] tag)
- [X] T005 [P] Create base configuration loader for `data/metadata.yaml` in `code/__init__.py`
- [X] T006 [P] Setup deterministic random seed utility in `code/utils.py` (global seed pinning)
- [X] T007 [P] Implement error handling wrapper for HTTP requests in `code/download.py` (retry logic)
- [X] T008 [P] Create logging infrastructure in `code/utils.py` to track pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download SPARC data, parse rotation curves, and filter for quality (inclination <10°, points ≥15)

**Independent Test**: Execute download and preprocessing scripts; verify output CSV has ≥15 points/galaxy and inclination uncertainty <10°. **Test Case**: Verify that if T016 (checksum verification) fails, the pipeline halts with a non-zero exit code and logs a fatal error.

### Implementation for User Story 1

**⚠️ CRITICAL SEQUENCE**: T012 -> T016 -> T013 -> T014 -> T015. Do NOT run in parallel.

- [X] T012 [US1] Implement SPARC downloader with a configurable retry logic mechanism (a limited number of attempts) in `code/download.py` (FR-001)
- [X] T016 [US1] Implement checksum verification and metadata logging for downloaded SPARC data in `data/metadata.yaml` per Constitution Principle III (Data Hygiene). **Dependency**: T012 must complete first. (FR-001, Constitution Principle III)
- [X] T013 [US1] Implement rotation curve parser in `code/preprocess.py` to extract radial distance, velocity, uncertainty. **Dependency**: T016 must complete first (requires verified data). (FR-002)
- [X] T014 [US1] Implement quality filter in `code/preprocess.py` to exclude inclination uncertainty ≥10° and <15 points. **Dependency**: T013 must complete first. (FR-003)
- [ ] T015 [US1] Create `data/processed/filtered_galaxies.csv` and update `data/metadata.yaml` with download timestamp/version. **Dependency**: T014 must complete first. **Error Handling**: If upstream artifacts (T014 output) are missing or invalid, log a fatal error and exit with non-zero code. (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Model Fitting and Goodness-of-Fit Computation (Priority: P2)

**Goal**: Fit MOND (simple) and NFW models to each galaxy; compute reduced χ², AIC, BIC; perform sensitivity analysis

**Independent Test**: Run fitting on a subset; verify metrics match analytical definitions and execute within 30s/galaxy.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement MOND 'simple' model in `code/models/mond.py`: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0) with a0=1.2e-10; include M/L (mass-to-light ratio) as a free parameter (FR-004, Plan Summary)
- [ ] T022 [P] [US2] {{claim:c_b0e61bcc}} **Note**: spec.md FR-005 text is defective (missing value); plan.md requires update to explicitly mandate this citation or include the value. (FR-005) <!-- FAILED: unspecified -->
- [X] T023 [US2] Implement fitting engine in `code/fit.py` using `scipy.optimize.curve_fit` with velocity uncertainty weighting. **Dependency**: T021 AND T022 must complete. (FR-006)
- [X] T024 [US2] Implement metric calculator in `code/metrics.py` for reduced χ², AIC, BIC (FR-007)
- [ ] T025 [US2] Generate `results/fit_summary.csv` with all metrics per galaxy-model. **Dependency**: T023 and T024 must complete. **Error Handling**: If upstream artifacts (T023/T024 output) are missing or invalid, log a fatal error and exit with non-zero code.
- [ ] T026 [US2] Implement sensitivity analysis in `code/sensitivity.py` sweeping χ² thresholds across a set of values and output `results/sensitivity_data.csv`. **Dependency**: T025 must complete. (FR-012, SC-006) **Note**: spec.md SC-006 text is defective (missing '1.0'); plan.md requires update to include the full set. <!-- FAILED: unspecified -->
- [ ] T035 [US2] Generate `results/sensitivity_summary.txt` with a text-based summary of the sensitivity sweep results (pass rates per threshold) derived from `results/sensitivity_data.csv`. **Dependency**: T026 must complete. (FR-012, SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Residual Analysis and Statistical Comparison (Priority: P3)

**Goal**: Analyze residuals, perform block-bootstrap permutation test, apply Holm-Bonferroni correction, and generate verdicts

**Independent Test**: Run residual analysis; verify block-bootstrap p-values and corrected p-values are produced and compared to alpha thresholds. **Test Case**: Verify the entire chain T031->T032->T033->T034 executes successfully and produces valid outputs.

### Implementation for User Story 3

- [X] T031 [US3] Implement residual calculator in `code/residuals.py` to compute (observed - predicted) distributions (FR-008)
- [ ] T032 [US3] Implement block-bootstrap permutation test in `code/residuals.py` resampling at galaxy level. (FR-009, US3)
- [ ] T033 [US3] Implement Holm-Bonferroni correction in `code/residuals.py` for multiple hypothesis tests. **Dependency**: T032 must complete. (FR-010)
- [ ] T034 [US3] Generate `results/residual_stats.csv` with mean, median, std, p-values per model. **Dependency**: T031, T032, T033 must complete. **Error Handling**: If upstream artifacts (T031/T032/T033 output) are missing or invalid, log a fatal error and exit with non-zero code.
- [ ] T036 [US3] Generate `results/analysis_verdict.md` by reading `results/residual_stats.csv` (T034 output) and `results/sensitivity_summary.txt` (T035 output) and applying the following logic: If p < 0.05, output "MOND preferred"; else if p > 0.95, output "NFW preferred"; else output "No significant difference". **Output Format**: Markdown file with sections for Methodology, Results, and Verdict. **Dependency**: T034 and T035 must complete. (SC-004, SC-005)
- [ ] T060 [P] [US3] Documentation updates in `docs/` (including the associational framing in paper text per FR-011). **Dependency**: T036 must complete. (FR-011)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T061 [P] Code cleanup and refactoring of `code/models/`, `code/residuals.py`
- [ ] T062 [P] Performance optimization: ensure fitting loop <30s/galaxy (memory profiling)
- [ ] T063 [P] Additional unit tests in `tests/unit/` covering edge cases (malformed files, convergence failures)
- [ ] T064 [P] Run `quickstart.md` validation and verify all checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires fit results from US2
- **Polish (Phase N)**: Depends on all desired user stories and revisions being complete

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Specific Task Dependencies

- **T050**: Depends on T048 AND T049 completion.
- **T012 -> T016 -> T013 -> T014 -> T015**: Strict sequential order in Phase 3.
- **T023**: Depends on T021 AND T022 completion.
- **T025**: Depends on T023 AND T024 completion.
- **T026**: Depends on T025 completion.
- **T035**: Depends on T026 completion.
- **T034, T036, T060**: Depend on T031, T032, T033 completion (T036 also depends on T035).
- **T061, T062, T063, T064**: Depend on all desired user stories completion.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T048 and T049 (Phase 2) can run in parallel
- Once Foundational phase completes, US1, US2, US3, and US4 can start in parallel (if team capacity allows)
- All tasks within a story marked [P] can run in parallel (where no dependencies exist)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Strictly sequential T012->T016->T013->T014->T015)
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
 - Developer A: User Story 1 (Data - Sequential)
 - Developer B: User Story 2 (Fitting + Sensitivity)
 - Developer C: User Story 3 (Statistics + Verdict + Documentation)
3. Stories complete and integrate independently