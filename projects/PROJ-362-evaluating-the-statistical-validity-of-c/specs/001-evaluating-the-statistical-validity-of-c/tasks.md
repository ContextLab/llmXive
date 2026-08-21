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

- [ ] T001 Create root project directory `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/` relative to repo root
- [ ] T001.1 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/__init__.py` (empty file)
- [ ] T001.2 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/main.py` (stub with argparse entry point)
- [ ] T001.3 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/config.py` (stub with placeholder constants)
- [ ] T002.1 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/requirements.txt` with pinned dependencies: `pandas`, `numpy`, `scipy`, `scikit-learn`, `tqdm`, `datasets`, `psutil`, `pytest`, `ruff`, `black`
- [ ] T002.2 [P] Create virtual environment (venv) in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/venv/`
- [ ] T002.3 [P] Install dependencies from `requirements.txt` into the virtual environment
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Robust and Web data via `datasets.load_dataset` with retry logic (3 attempts, exponential backoff: 1s, 2s, 4s). MUST include fallback to specific NIST archive paths: ` and ` (verified accessible via static archive). Enforce CPU-only execution (per spec FR-001, FR-012). Raise error if real fetch fails (no synthetic fallback).
- [ ] T005 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/contracts/dataset.schema.yaml` defining qrels structure. Path: `projects/PROJ-362-evaluating-the-statistical-validity-of-c/contracts/dataset.schema.yaml`. Content:
```yaml
type: object
properties:
 query_id:
 type: integer
 doc_id:
 type: integer
 relevance:
 type: integer
required:
 - query_id
 - doc_id
 - relevance
```
- [ ] T006 [P] Implement validation logic in `projects/PROJ-evaluating-the-statistical-validity-of-c/code/data_loader.py` to enforce schema compliance (referencing `contracts/dataset.schema.yaml`) and log warnings for zero-relevance queries. Depends on: T005
- [ ] T007 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/config.py` with constants for seeds, permutation counts (N=1000), batch sizes, and memory thresholds. Include: `PERMUTATION_N`, `SEED`, `BATCH_SIZE`, `MEMORY_THRESHOLD_GB` (a configurable memory limit), `RUNTIME_THRESHOLD_HOURS` (5.0), `DATA_RAW_PATH`, `RESULTS_PATH`.
- [ ] T008.1 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/metrics.py` function `ndcg_at_k` for NDCG@10 calculation using IDCG normalization.
- [ ] T008.2 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/metrics.py` function `map_at_k` for MAP calculation.
- [ ] T008.3 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/metrics.py` function `idcg_at_k` for normalization.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Permutation Test Execution (Priority: P1) 🎯 MVP

**Goal**: Execute permutation tests on TREC data to generate null distributions and p-values for NDCG@10 and MAP.

**Independent Test**: Run `main.py` with `--mode permutation` on a single query; verify `results/null_distributions/` contains CSVs and `results/p_values/` contains raw p-values.

### Test Definition for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: Tests are written first but require the presence of stubs from T013-T018 to execute.*

- [ ] T010 [P] [US1] Unit test for `metrics.py` NDCG@10 calculation with known ground truth in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_metrics.py`; Requires presence of stub in T008.1
- [ ] T011 [P] [US1] Unit test for permutation logic (shuffle correctness) in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_permutation.py`; Requires presence of stub in T013
- [ ] T012 [US1] Integration test: Verify p-value calculation `(r+1)/(N+1)` against a manual calculation in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/integration/test_permutation_flow.py`; Requires presence of stubs in T013, T016

### Implementation for User Story 1

- [ ] T013 [US1] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` core engine:
 1. Shuffle relevance labels N=1000 times per query.
 2. **Log the ACTUAL count of permutations executed (N_actual) to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/logs/permutation.log` in JSON format: `{"event": "permutation_complete", "query_id": "...", "N_actual": <actual_count>}`. Use log level INFO.**
 3. **Sub-task (Runtime Monitor): Integrate runtime/memory monitoring into the execution loop. Use `psutil` (memory) and `time.time()` (duration) with periodic sampling at regular intervals. Monitor `psutil.Process(os.getpid()).memory_info().rss`. If runtime > 5.0 hours (per FR-011) OR memory > 6 GB, trigger subsampling (random selection of a subset of queries). **Note: While Plan allocates 4.0h, FR-011 mandates 5.0h as the hard limit for subsampling to ensure sufficient permutations.** **Depends on: T007 (config values)**.
 4. Compute NDCG@10 and MAP for all permutations.
 5. **Depends on: T008.1, T008.2, T008.3 (metrics implementation)**.
- [ ] T014 [US1] Implement batch processing loop in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` to handle memory limits (process queries in batches, log progress). Depends on: T013
- [ ] T016 [US1] Implement p-value calculation logic: rank observed score within null distribution (depends on T013 completion). Formula: `(r + 1) / (N_actual + 1)`.
- [ ] T017 [US1] Save null distribution CSVs to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/null_distributions/` with headers `query_id, metric, score`.
- [ ] T018 [US1] Save raw p-values to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/p_values/raw_p_values.csv` with headers `query_id, metric, raw_p`.

---

## Phase 4: User Story 2 - Power Analysis & Inference Framing (Priority: P2)

**Goal**: Calculate MDES using label swapping, apply BH correction, and frame findings as associational.

**Independent Test**: Run `main.py` with `--mode power_analysis`; verify `results/mdes/` contains MDES estimates and `results/p_values/corrected_p_values.csv` exists.

### Test Definition for User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Note: Tests are written first but require the presence of stubs from T021 to execute.*

- [ ] T019 [P] [US2] Unit test for bootstrap resampling and label-swapping functions in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_power_analysis.py`; Requires presence of stub in T021
- [ ] T020 [P] [US2] Unit test for Benjamini-Hochberg implementation against `statsmodels.stats.multitest` in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_bh_correction.py`
- [ ] T025.1 [P] [US2] **Verification**: Run `tests/integration/test_mdes_stability.py` to read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` and **assert ci_width < 0.02 for BOTH NDCG@10 and MAP metrics independently**; if threshold is exceeded, **report and flag instability** but do NOT fail the build (research outcome); **Depends on: T021** (completion of T021 output file)

### Implementation for User Story 2

- [ ] T021 [US2] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/power_analysis.py` MDES logic:
 1. Implement bootstrap resampling utility for power estimation.
 2. **Implement alternative hypothesis simulation by 'swapping top-k positions' in relevance labels (per spec FR-006). Note: FR-006 mandates swapping; this overrides the plan's 'noise injection' description.**
 3. Perform binary search over effect sizes (initial range [0.001, 0.500], tolerance ≤ 0.001 on metric delta) to find smallest shift detectable with Power ≥ 0.8. **Effect size is defined as the delta in metric scores (NDCG@10 or MAP), not label deltas.**
 4. **Write MDES result to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` with columns `metric, mdes, power, ci_width`**.
 **Depends on: None (Independent of T018, runs in parallel with T023)**.

- [ ] T023 [US2] Implement BH correction in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/power_analysis.py`: apply separately to NDCG and MAP p-value families (two families). **Depends on: T018** (explicitly depends on completion of T018 raw p-values)
- [ ] T026 [US2] Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/p_values/corrected_p_values.csv` with columns: `query_id, metric, raw_p, corrected_p, is_significant`
- [ ] T024 [US2] Implement sensitivity analysis: **iterate (sweep) alpha values across a low-range interval inclusive with fine-grained resolution**. Report the count of queries where significance status changes between adjacent α values. **Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/sensitivity/alpha_sweep.csv` with columns `alpha, significant_count, status_change_count`**. **Depends on: T013, T016, T018, T023** (completion of T023 output and raw data from T013/T016)
- [ ] T027 [US2] Add explicit text generation in `main.py` output: "Findings indicate statistical association, not causal algorithmic improvement" per FR-008

### Validation for User Story 2

- [ ] T025.1 [US2] **Verification**: Run `tests/integration/test_mdes_stability.py` to read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` and **assert ci_width < 0.02 for BOTH NDCG@10 and MAP metrics independently**; if threshold is exceeded, **report and flag instability** but do NOT fail the build (research outcome); **Depends on: T021** (completion of T021 output file)

---

## Phase 5: User Story 3 - Reporting & Visualization (Priority: P3)

**Goal**: Produce CSV summaries, PNG density plots, and enforce runtime/memory constraints.

**Independent Test**: Run `main.py` with `--mode report`; verify `results/plots/` contains PNGs and `results/summary.csv` exists.

### Test Definition for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test: Verify memory usage stays < 7GB during full run in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/visualization.py` to generate density plots comparing original vs. permuted scores
- [ ] T030 [US3] Annotate plots with MDES and significance thresholds: **Modify `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/visualization.py` to add a vertical dashed line at `mdes` value (read from `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` column `mdes`) and text label "MDES={val}" to all density plots in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/plots/`; use font family 'DejaVu Sans'**; **Depends: T021** (reads MDES value from T021 output)
- [ ] T031 [US3] Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/summary.csv` aggregating all query-metric pairs, p-values, and MDES; **Depends on: T018, T023, T021** (explicitly lists all producers)
- [ ] T033 [US3] Add error handling for network failures in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` (graceful exit with error code)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Update `README.md` with sections: 'Installation', 'Usage', 'Output Artifacts'
- [ ] T035 Code cleanup: Remove debug prints and ensure logging levels are appropriate
- [ ] T036 Performance optimization: Verify batch processing logic is efficient; **Ensure memory < 6GB during batch of 50 queries**
- [ ] T037 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly
- [ ] T038 [P] Add content checksums to `data/raw/` and `results/` artifacts for reproducibility (Constitution Principle V); **Mechanism**: Implement a script to **read all files in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/data/raw/` and `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/`, sort the list of all discovered files by their full relative path string in ascending ASCII order, compute SHA-256 hash for each, and append the results to `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map (flat structure: `relative_path: sha256_hash`)**; **Depends on: T017, T018, T021, T023, T026, T029, T030, T031** (completion of all artifact generation tasks)

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

### Test Execution Note

- Tests (T010-T012, T019-T020, T028) are defined first in the file.
- **Execution Order**: Implementation tasks (T013-T018, T021, T023, T029-T031) must provide **stubs** before Tests can be executed.
- The file order reflects "Definition First", but the **execution flow** requires:
 1. Write Stubs (T013-T018, T021, etc.)
 2. Run Tests (T010-T012, etc.)
 3. Complete Implementation (T013-T018, T021, etc.)
 4. Verify Tests Pass.

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