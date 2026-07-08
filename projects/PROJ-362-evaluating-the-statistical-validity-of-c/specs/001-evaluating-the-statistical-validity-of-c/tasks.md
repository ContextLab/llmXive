# Tasks: Evaluating the Statistical Validity of Common Ranking Metrics

**Input**: Design documents from `/specs/001-statistical-validity-ranking-metrics/`
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

- [ ] T001 Create root project structure including `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/` directory and `__init__.py`
- [ ] T001.1 [P] Create `code/__init__.py` (empty file)
- [ ] T001.2 [P] Create `code/main.py` (stub with argparse entry point)
- [ ] T001.3 [P] Create `code/config.py` (stub with placeholder constants)
- [ ] T002 Initialize Python 3.10 project with pinned dependencies (`requirements.txt`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `data_loader.py` to fetch TREC Robust and Web data via `datasets.load_dataset` with retry logic (multiple attempts)
- [ ] T005 [P] Create `contracts/dataset.schema.yaml` defining qrels structure: `type: object, properties: {query_id: {type: integer}, doc_id: {type: integer}, relevance: {type: integer}}`
- [ ] T006 [P] Implement validation logic in `data_loader.py` to enforce schema compliance and log warnings for zero-relevance queries <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 4, column 1:
 **Input**: Design documents from...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 4, column 2:
 **Input**: Design documents from...
 ^) -->
- [~] T007 [P] Create `config.py` with constants for seeds, permutation counts (N=1000), batch sizes, and memory thresholds
- [~] T008 [P] Implement `metrics.py` with a CPU-only NDCG@k calculation function using IDCG normalization and explicit relevance label mapping
- [ ] T008.1 [P] Implement `metrics.py` with CPU-only MAP calculation function using IDCG normalization and explicit relevance label mapping
- [~] T009 Setup environment configuration management (paths for `data/raw/`, `results/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Permutation Test Execution (Priority: P1) 🎯 MVP

**Goal**: Execute permutation tests on TREC data to generate null distributions and p-values for NDCG@10 and MAP.

**Independent Test**: Run `main.py` with `--mode permutation` on a single query; verify `results/null_distributions/` contains CSVs and `results/p_values/` contains raw p-values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T010 [P] [US1] Unit test for `metrics.py` NDCG@10 calculation with known ground truth in `tests/unit/test_metrics.py`
- [~] T011 [P] [US1] Unit test for permutation logic (shuffle correctness) in `tests/unit/test_permutation.py`
- [~] T012 [US1] Integration test: Verify p-value calculation `(r+1)/(N+1)` against a manual calculation in `tests/integration/test_permutation_flow.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `permutation.py` core engine: shuffle relevance labels N=1000 times per query and **log the ACTUAL count of permutations executed (N_actual) used in the p-value calculation, not just the target**
- [~] T014 [US1] Implement batch processing loop in `permutation.py` to handle memory limits (process queries in batches, log progress)
- [~] T015 [US1] Implement runtime monitor in `main.py`: if runtime > 3.5h, trigger subsampling (random selection of 100 queries) per FR-011; runs concurrently or depends on T013 completion
- [~] T016 [US1] Implement p-value calculation logic: rank observed score within null distribution (depends on T013 completion)
- [~] T017 [US1] Save null distribution CSVs to `results/null_distributions/` with headers `query_id, metric, score`
- [~] T018 [US1] Save raw p-values to `results/p_values/raw_p_values.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Power Analysis & Inference Framing (Priority: P2)

**Goal**: Calculate MDES using swapping top-k positions, apply BH correction, and frame findings as associational.

**Independent Test**: Run `main.py` with `--mode power_analysis`; verify `results/mdes/` contains MDES estimates and `results/p_values/corrected_p_values.csv` exists.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for top-k swapping function (simulating alternative hypothesis) in `tests/unit/test_power_analysis.py`
- [~] T020 [P] [US2] Unit test for Benjamini-Hochberg implementation against `statsmodels.stats.multitest` in `tests/unit/test_bh_correction.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement `power_analysis.py` bootstrap resampling utility function for power estimation; **prerequisite for T021**
- [ ] T022.1 [US2] Implement `power_analysis.py` function to simulate alternative hypothesis by **swapping top-k positions** in relevance labels
- [~] T021 [US2] Implement `power_analysis.py` MDES logic: binary search over the magnitude of the **top-k swap** to find smallest shift detectable with Power ≥ 0.8; **calls the bootstrap function (T022) and swap function (T022.1) iteratively**; search range [0.001, 0.500], tolerance ≤ 0.001, Power = proportion of rejections; **Write MDES result to `results/mdes/mdes_summary.csv` with columns `metric, mdes, power, ci_width`**
- [~] T023 [US2] Implement BH correction in `power_analysis.py`: apply separately to NDCG and MAP p-value families; **Depends on: T018**
- [~] T024 [US2] Implement sensitivity analysis: **iterate (sweep) alpha values across [0.01, 0.05, 0.10]**, report the count of queries where significance status changes between α values; **Generate `results/sensitivity/alpha_sweep.csv` with columns `alpha, significant_count`**; **Depends on: T023**
- [~] T025 [US2] Generate `results/mdes/mdes_summary.csv` with columns: `metric, mdes, power, ci_width`
- [ ] T025.1 [US2] **Verification**: Read `results/mdes/mdes_summary.csv` and **assert ci_width < 0.02 for BOTH NDCG@10 and MAP metrics independently**; fail the build if either exceeds threshold (SC-003)
- [~] T026 [US2] Generate `results/p_values/corrected_p_values.csv` with columns: `query_id, metric, raw_p, corrected_p, is_significant`
- [~] T027 [US2] Add explicit text generation in `main.py` output: "Findings indicate statistical association, not causal algorithmic improvement" per FR-008

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reporting & Visualization (Priority: P3)

**Goal**: Produce CSV summaries, PNG density plots, and enforce runtime/memory constraints.

**Independent Test**: Run `main.py` with `--mode report`; verify `results/plots/` contains PNGs and `results/summary.csv` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Integration test: Verify memory usage stays < 7GB during full run in `tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `visualization.py` to generate density plots comparing original vs. permuted scores
- [ ] T030 [US3] Annotate plots with MDES and significance thresholds: **Modify `visualization.py` to add a vertical dashed line at `mdes` value and text label "MDES={val}" to all density plots in `results/plots/`**
- [ ] T031 [US3] Generate `results/summary.csv` aggregating all query-metric pairs, p-values, and MDES
- [ ] T032 [US3] Implement final runtime/memory guard in `main.py`: if > 5h or > 6GB RAM, force subsampling and log warning
- [ ] T033 [US3] Add error handling for network failures in `data_loader.py` (graceful exit with error code)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Update `README.md` with sections: 'Installation', 'Usage', 'Output Artifacts'
- [ ] T035 Code cleanup: Remove debug prints and ensure logging levels are appropriate
- [ ] T036 Performance optimization: Verify batch processing logic is efficient; **Ensure memory < 6GB during batch of 50 queries**
- [ ] T037 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly
- [ ] T038 Add content checksums to `data/raw/` and `results/` artifacts for reproducibility (Constitution Principle V)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Critical**: Must complete before US2 to provide null distributions.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (null distributions) for power analysis.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 output for reporting.

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
Task: "Unit test for metrics.py NDCG@10 calculation in tests/unit/test_metrics.py"
Task: "Unit test for permutation logic in tests/unit/test_permutation.py"

# Launch core implementation tasks:
Task: "Implement permutation.py core engine in src/permutation.py"
Task: "Implement batch processing loop in src/permutation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Permutation Test)
4. **STOP and VALIDATE**: Test US1 independently (generate null distributions)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (MDES, BH correction) → Deploy/Demo
4. Add User Story 3 → Test independently (Plots, Summary) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Permutation Engine)
 - Developer B: User Story 2 (Power Analysis) - *Note: Must wait for US1 data for full integration, but can mock data for dev*
 - Developer C: User Story 3 (Reporting) - *Note: Can build visualization logic with mock data*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on a limited number of CPU cores, a constrained amount of RAM, and without GPU acceleration. Avoid any heavy model loading or 8-bit quantization.
- **Data Integrity**: All data must come from verified TREC sources (HuggingFace/NIST). No synthetic data generation for input metrics.