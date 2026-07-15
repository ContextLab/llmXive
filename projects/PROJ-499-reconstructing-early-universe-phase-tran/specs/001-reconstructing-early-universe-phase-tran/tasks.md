# Tasks: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

**Input**: Design documents from `/specs/001-reconstructing-early-universe-phase-tran/`
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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-499-reconstructing-early-universe-phase-tran/`) with the following exact directories: `data/raw`, `data/derived`, `data/synthetic`, `code`, `tests/unit`, `tests/integration`, `tests/contract`, `docs`, `state`.
- [X] T002 Initialize a Python project with `requirements.txt` (pinning `healpy==1.16.5`, `dynesty==2.1.3`, `emcee==3.1.6`, `numpy==1.24.3`, `scipy==1.11.4`, `requests==2.31.0`, `pyyaml==6.0.1`, `astropy==5.3.4`, `astroquery==0.4.6`).
- [X] T003a [P] Create `.flake8` configuration file with `max-line-length=88`, `ignore=E203,W503`, and `exclude=venv,.git`.
- [X] T003b [P] Create `pyproject.toml` section for `black` with `line-length=88` and `target-version=['py311']`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/` directory structure (`raw/`, `derived/`, `synthetic/`) and `.gitignore` for large files
- [X] T005 [P] Implement `code/utils.py` with the following exact function signatures:
 - `verify_checksum(file_path: str, expected_hash: str) -> bool`: Uses SHA-256 to verify file integrity.
 - `retry_download(url: str, max_retries: int = 3, base_delay: float = 1.0) -> bytes`: Implements exponential backoff logic.
 - **Constitution Check**: Ensure `verify_checksum` is used to satisfy Constitution Principle III (Data Hygiene).
- [ ] T006 [P] Setup `code/` module structure with `__init__.py` and relative import configuration
- [ ] T007 Create base configuration loader in `code/config.py` to handle `random.seed` pinning and CPU-only constraints, and to store verified dataset URLs (keys: `PLANCK_MAP_ID`, `BICEP_URL`).
- [ ] T008 Setup `tests/` directory structure (`unit/`, `integration/`, `contract/`) with `pytest.ini`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0.5: Synthetic Validation (GATED)

**Purpose**: Validate the pipeline against synthetic data BEFORE processing real data.
**GATE**: This phase MUST pass before Phase 1 begins.
**Note**: This phase now correctly depends on Phase 1 (Foundational) being complete.

- [ ] T024 [US2] Implement `code/synthetic_data.py` to generate ground truth datasets for Inflation ($r=0.01$) and Phase Transition ($E_{PT}=10^{15}$ GeV) models with known noise characteristics.
- [ ] T025a [US2] Implement `code/validation.py` to run the pipeline on synthetic Inflation data and verify that the posterior distribution for $r$ covers the true value within the 95% credible interval and is centered within 10%. **Metric**: Check if true_value is within [percentile_2.5, percentile_97.5] and |(mean - true)|/true < 0.10 (SC-005, US2 Acceptance 1).
- [ ] T025b [US2] Implement `code/validation.py` to run the pipeline on synthetic Phase Transition data and verify that the posterior distribution for $E_{PT}$ covers the true value within the 95% credible interval and is centered within 10%. **Metric**: Check if true_value is within [percentile_2.5, percentile_97.5] and |(mean - true)|/true < 0.10 (SC-005, US2 Acceptance 1).
- [X] T025c [US2] Implement `code/validation.py` to verify that the Bayes factor correctly distinguishes between models by exceeding the decision threshold ($K > 10$) for the ground truth model in both synthetic cases (SC-002, SC-003).

**Checkpoint**: Synthetic Validation complete. Pipeline is validated. Proceed to Phase 1 only if T025a/b/c pass.

---

## Phase 2: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, mask, and prepare Planck 2015 and BICEP/Keck B-mode polarization maps to compute clean angular power spectra.

**Independent Test**: The pipeline can be fully tested by running it on a subset of the sky (e.g., a single HEALPix patch) and verifying that the output power spectrum matches known theoretical expectations for lens-only B-modes in that region.

### Tests for User Story 1 (TDD First) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data download integrity in `tests/contract/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for masked map generation in `tests/integration/test_masking.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/data_ingestion.py` to download Planck SMICA B-mode maps and BICEP/Keck spectra. **Input**: Read `PLANCK_MAP_ID` and `BICEP_URL` from `code/config.py`. **Dependencies**: Call `retry_download` and `verify_checksum` from `code/utils.py` (T005). **Output**: Store downloaded files in `data/raw/` and SHA-256 checksums in `data/hashes.json`. Implement retry logic for corrupted downloads.
- [X] T013 [US1] Implement `code/data_ingestion.py` to apply Planck 2015 Common Mask to B-mode maps (FR-002).
- [X] T014 [US1] Implement `code/spectrum_computation.py` to compute $C_\ell^{BB}$ from masked maps using `pyHEALPix` (healpy) in CPU-only mode (FR-003).
- [~] T015 [US1] Add validation logic to verify sky coverage. **Metric**: `coverage = non-masked pixels / total pixels`. **Behavior**: **Raise ValueError** if `coverage < 0.70`. (Satisfies US1 Acceptance Scenario 1, SC-001).
- [~] T016 [US1] Add logging for data ingestion and masking operations with checksum verification status.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Theoretical Model Generation and Fitting (Priority: P2)

**Goal**: Generate theoretical B-mode power spectra for inflationary, phase transition, and null models, and fit them to observed data using CPU-tractable Nested Sampling.

**Independent Test**: The fitting routine can be tested independently by generating synthetic data from a known model (e.g., $r=0.01$ inflation) and verifying that the sampler recovers the input parameters within 1$\sigma$ confidence intervals.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_model_generation.py`
- [X] T019 [P] [US2] Integration test for Nested Sampling convergence in `tests/integration/test_inference.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/model_generation.py` to generate theoretical spectra. **Input**: Grid of $r$ over a relevant small-range interval and $E_{PT} \in [10^{14}, 10^{16}]$ GeV (log scale). **Output**: JSON file with exact schema: `{"model_type": str, "params": dict, "l_values": list[int], "cl_values": list[float]}` (FR-004).
- [X] T021a [US2] Implement `code/inference.py` using `dynesty` (Nested Sampling) with limited live points (e.g., 50 (1904.02180, https://arxiv.org/abs/1904.02180)) for CPU feasibility to estimate posteriors for $r$ and $E_{PT}$ (Plan requirement, FR-005).
- [X] T022 [US2] Implement `code/inference.py` to detect non-convergence (evidence estimate instability) and log warnings or extend the run (Edge Case).
- [X] T023 [US2] Implement `code/inference.py` to clamp model predictions for $\ell < 2$ and flag extrapolated points (Edge Case).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Model Comparison and Statistical Validation (Priority: P3)

**Goal**: Compute Bayes factors using Nested Sampling and perform null tests using independent sky patches to distinguish between models.

**Independent Test**: The validation suite can be tested by splitting synthetic data into two halves, running the full analysis on each, and verifying that the Bayes factors and parameter estimates are consistent within statistical fluctuations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for Bayes factor precision in `tests/contract/test_model_comparison.py`
- [X] T027 [P] [US3] Integration test for sky patch consistency in `tests/integration/test_sky_split.py`

### Implementation for User Story 3

- [X] T028a [P] [US3] Implement `code/model_comparison.py` to compute Bayes factors via `dynesty` evidence calculation for Inflation vs. Phase Transition vs. Null (Plan requirement, FR-006).
- [X] T029 [US3] Implement `code/validation.py` to split sky into independent patches (Northern/Southern) and verify consistency of best-fit $r$ values (FR-007).
- [X] T030 [US3] Implement `code/model_comparison.py` to report Bayes factor $K$ with 2 decimal places precision and decision thresholds ($K > 10$) (US3 Acceptance 1).
- [X] T031 [US3] Add plotting functionality in `code/plotting.py` to visualize posteriors and Bayes factors for all models.
- [~] T032 [US3] Implement `code/utils.py` to generate `data/derived/model_comparison_results.json` with exact schema from contracts/

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038a [P] Update `docs/quickstart.md` with new CLI flags and execution steps.
- [~] T038b [P] Update `docs/data-model.md` with schema changes and `docs/research.md` with final results (Phase 0.5 and Phase 1-3 outcomes). <!-- ATOMIZE: requested -->
- [X] T039 Code cleanup and refactoring for CPU efficiency: **Deliverable**: Reduce cyclomatic complexity of `code/inference.py` to a level that ensures maintainability and computational efficiency.
- [~] T040 Performance optimization across all stories: **Deliverable**: Complete a 1000-step `dynesty` run on Nside=64 synthetic data within 2 hours on CPU.
- [~] T041 [P] Additional unit tests for edge cases in `tests/unit/`
- [~] T042 Security hardening for data download URLs
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end pipeline execution within 6 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately
- **Phase 1 (Foundational)**: Depends on Phase 0 completion - BLOCKS all user stories and Phase 0.5
- **Phase 0.5 (Synthetic Validation)**: Depends on Phase 1 completion. **GATE**: Must pass before Phase 2.
- **Phase 2 (US1)**: Depends on Phase 1 completion
- **Phase 3 (US2)**: Depends on Phase 1 completion (can use synthetic data for validation without real data)
- **Phase 4 (US3)**: Depends on Phase 3 completion
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on US1 data ingestion for real data, but can use synthetic data for validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on US2 for model fitting results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data download integrity in tests/contract/test_data_ingestion.py"
Task: "Integration test for masked map generation in tests/integration/test_masking.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download Planck 2015 SMICA B-mode maps"
Task: "Implement code/data_ingestion.py to apply Planck 2015 Common Mask"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational
3. Complete Phase 0.5: Synthetic Validation (GATED)
4. Complete Phase 2: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
- **Critical**: Phase 0.5 Synthetic Validation (T024, T025a/b/c) MUST pass before any observational data is processed (Plan Gate).
- **Critical**: All tasks must run on CPU-only (2 cores, 7GB RAM) within 6 hours.
- **Critical**: No fake data; all synthetic data must be generated from known ground truth models.
- **Critical**: Primary inference engine is `dynesty` (Nested Sampling) as per Plan and updated Spec (FR-005, FR-006).
- **Critical**: Phase 5 (Reviewer Response) has been removed as it was based on hallucinated requirements.