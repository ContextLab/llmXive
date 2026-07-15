# Tasks: Fractal Dimension and Energy Dissipation in Turbulent Flows

**Input**: Design documents from `/specs/001-fractal-dimension-turbulence/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure with specific files: `projects/PROJ-051-investigating-the-relationship-between-f/code/__init__.py`, `config.py`, `main.py`, `requirements.txt`, `README.md`, and directories `data/`, `analysis/`, `validation/`, `tests/`
- [ ] T002 Initialize Python 3.10 project with dependencies: `numpy`, `scipy`, `scikit-learn`, `pandas`, `requests`, `tqdm`, `h5py`, `matplotlib`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `config.py` to manage Re_λ values (representing a range of low to high turbulence intensities), vorticity thresholds, and memory limits (max constrained RSS)
- [ ] T005 [P] Implement `utils/logging.py` for reproducible logging with random seeds and step timing
- [ ] T006 [P] Setup `contracts/` directory with `analysis_output.schema.yaml` defining output fields for D_f, ε, and correlation results
- [ ] T007 Create `data/download.py` with JHTDB fetcher logic and Phase-Shifted DNS fallback mechanism; explicitly ensure fallback logic calls `validation/null_model.py` (fallback applies ONLY when JHTDB is unavailable and for algorithm validation only, never for primary hypothesis testing)
- [ ] T008 Create `data/preprocess.py` implementing streaming/chunked processing for 512³ grids to enforce memory constraints
- [~] T009 Implement `main.py` CLI entry point with pipeline orchestration and contract validation step

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Fractal Dimension Computation (Priority: P1) 🎯 MVP

**Goal**: Compute fractal dimensions of vorticity iso-surfaces using a box-counting algorithm on CPU.

**Independent Test**: Verify D_f matches ground truth (Menger sponge, D=2.73) within ±0.05. [UNRESOLVED-CLAIM: c_4931a208 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for box-counting output schema in `tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Unit test for Menger sponge ground truth in `tests/unit/test_fractal.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `analysis/fractal.py` with box-counting algorithm supporting configurable vorticity thresholds
- [ ] T013 [US1] Implement logic in `analysis/fractal.py` to handle edge cases: reject thresholds yielding no surfaces or space-filling results
- [ ] T014 [US1] Implement `validation/synthetic_menger.py` to generate Menger sponge data for ground-truth testing
- [ ] T015 [US1] Implement sensitivity analysis logic in `analysis/fractal.py` to sweep thresholds **{2×, 3×, 4× RMS}** (explicitly excluding ambiguous placeholders) and report correlation coefficient variation across these specific values as required by FR-008 and SC-005
- [ ] T016 [US1] Add validation in `analysis/fractal.py` to ensure 2.0 ≤ D_f ≤ 3.0

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Energy Dissipation Rate Computation (Priority: P1)

**Goal**: Compute local energy dissipation rate ε from strain rate tensors derived from DNS velocity fields.

**Independent Test**: Verify ε matches Taylor-Green vortex analytical solution within ≤1% relative error. [UNRESOLVED-CLAIM: c_a2c8d7ba — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Taylor-Green vortex in `tests/unit/test_dissipation.py`
- [ ] T019 [P] [US2] Integration test for laminar flow near-zero check in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `analysis/gradients.py` to compute velocity gradient tensors ∇u using central finite-difference schemes of appropriate order and precision as mandated by FR-002
- [ ] T021 [US2] Implement `analysis/dissipation.py` to calculate ε = 2νS_ijS_ij using kinematic viscosity ν from metadata (FR-004)
- [ ] T022 [US2] Implement `validation/synthetic_taylor_green.py` to generate analytical Taylor-Green vortex data
- [ ] T023 [US2] Add validation in `analysis/dissipation.py`: **If Re_λ < 300, skip intermittency ratio check and log warning; otherwise, verify max(ε)/mean(ε) ≥ 1000** (SC-002). Do not hard-fail on low-Re data.
- [ ] T024 [US2] Integrate `data/preprocess.py` (completed module T008) streaming logic into `analysis/dissipation.py` to handle 512³ grids within 6GB RAM

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Testing (Priority: P2)

**Goal**: Perform linear regression between D_f and log(ε) with block-bootstrapping and FWE correction.

**Independent Test**: Verify Pearson r and p-value are computed correctly with n≥100 independent samples. [UNRESOLVED-CLAIM: c_a1b79c2a — status=not_enough_info]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for block-bootstrap CI calculation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Contract test for correlation output schema in `tests/contract/test_schemas.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `analysis/stats.py` with Pearson correlation and linear regression functions
- [ ] T029 [US3] Implement block-bootstrapping logic in `analysis/stats.py` to handle spatially correlated data (n=1000 resamples)
- [ ] T030 [US3] Implement family-wise error correction (Bonferroni or Benjamini-Hochberg) in `analysis/stats.py`
- [ ] T030B [P] [US3] Implement logic in `analysis/stats.py` to compute/estimate integral length scale (λ) from velocity field (PREREQUISITE for T031)
- [ ] T031 [US3] **DEPENDS ON: T030B**. Implement logic to select spatial subdomains separated by ≥10 integral length scales (λ) using the computed λ from T030B
- [ ] T031B [US3] **DEPENDS ON: T031**. Implement logic to count selected subdomains; if count < 100, log critical error and halt pipeline (enforcing FR-005/SC-004)
- [ ] T032 [US3] Implement `validation/null_model.py` (Phase-Shifted DNS) to decouple geometric thresholding from energetic magnitude
- [ ] T033 [US3] **DEPENDS ON: T015, T021**. Implement robustness check by computing D_f-ε correlation across **two distinct methods: (1) normalized RMS thresholding, (2) absolute vorticity thresholding**. Output a CSV row comparing the two correlation coefficients to verify the relationship is not an artifact.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Reynolds Number Scaling Analysis (Priority: P3)

**Goal**: Repeat analysis across Re_λ = 200, 400, 600 and test for scaling laws. [UNRESOLVED-CLAIM: c_a892279e — status=not_enough_info]

**Independent Test**: Verify scaling exponent α is estimated with uncertainty bounds.

### Implementation for User Story 4

- [ ] T034 [P] [US4] Extend `config.py` to support multi-Re_λ pipeline execution
- [ ] T035 [US4] **DEPENDS ON: T012, T021**. Implement logic to compute D_f ~ Re_λ^α scaling law and a confidence interval for α. **Explicitly write a 'null_finding' boolean flag and a message to the results JSON/CSV if α ≈ 0 within CI** as required by US-4 Scenario 3.
- [ ] T036 [US4] Implement logic to handle unsupported Re_λ values (log warning and skip)
- [ ] T036B [US4] **DEPENDS ON: T007**. Implement logic to detect if fallback data (Phase-Shifted DNS) is being used for Re-scaling; if so, log a "Deviation Report" stating H3 is unverified per plan constraints.
- [ ] T037 [US4] Aggregate results from `data/results/` across Re_λ datasets and generate scaling summary

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure resource compliance.

- [ ] T038 [P] Implement memory profiling in `main.py` to assert peak RSS ≤ 6 GB at each step
- [ ] T039 [P] Implement runtime profiling in `main.py` to assert total runtime ≤ 6 hours and step runtime ≤ 30 minutes
- [ ] T040 [P] Write comprehensive `docs/README.md` with instructions for running the pipeline on CI
- [ ] T041 [P] Add `requirements.txt` with pinned versions
- [ ] T042 [P] Run `pytest` with coverage report to ensure >80% coverage on core modules
- [ ] T043 [P] Validate `data/results/correlation_results.csv` against `contracts/analysis_output.schema.yaml` in `main.py`
- [ ] T044 [P] Run quickstart.md validation (if created in Phase 1)

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US3 (for integration) but calculation logic depends on US1/US2

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
Task: "Contract test for box-counting output schema in tests/contract/test_schemas.py"
Task: "Unit test for Menger sponge ground truth in tests/unit/test_fractal.py"

# Launch all implementation for User Story 1 together:
Task: "Implement analysis/fractal.py with box-counting algorithm"
Task: "Implement validation/synthetic_menger.py to generate Menger sponge data"
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