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

- [ ] T001.1 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/__init__.py` (empty file)
- [ ] T001.2 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/main.py` (stub with argparse entry point)
- [ ] T001.3 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/config.py` (stub with placeholder constants)
- [ ] T002.1 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/requirements.txt` with pinned dependencies: `pandas`, `numpy`, `scipy`, `scikit-learn`, `tqdm`, `ir-datasets`, `psutil`, `pytest`, `ruff`, `black`
- [ ] T002.2 [P] Create virtual environment (venv) in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/venv/`
- [ ] T002.3 [P] Install dependencies from `requirements.txt` into the virtual environment
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

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
- [ ] T004.1 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Robust 2004 data. **Primary Source**: `ir_datasets.load('trec/robust04')`. **Logic**: Attempt NIST fetch via `ir-datasets`. If `ir-datasets` fails (network error, 404, etc.), retry with exponential backoff (base_delay=2s, multiplier=2.0, max_retries=3). If NIST still fails after retries, **raise `RuntimeError` immediately**. **DO NOT** fall back to Hugging Face, synthetic, or mock data. **Post-Fetch Step**: Compute SHA-256 checksum of the downloaded file and update `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map. **Depends on: T005**.
- [ ] T004.2 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Web 2009 data. **Primary Source**: `ir_datasets.load('trec/web-track-2009')`. **Logic**: Attempt NIST fetch via `ir-datasets`. Retry with exponential backoff (base_delay=2s, multiplier=2.0, max_retries=3). If NIST still fails after retries, **raise `RuntimeError` immediately**. **DO NOT** fall back to Hugging Face, synthetic, or mock data. **Post-Fetch Step**: Compute SHA-256 checksum of the downloaded file and update `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map. **Depends on: T005**.
- [ ] T004.3 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Web 2010 data. **Primary Source**: `ir_datasets.load('trec/web-track-2010')`. **Logic**: Attempt NIST fetch via `ir-datasets`. Retry with exponential backoff (base_delay=2s, multiplier=2.0, max_retries=3). If NIST still fails after retries, **raise `RuntimeError` immediately**. **DO NOT** fall back to Hugging Face, synthetic, or mock data. **Post-Fetch Step**: Compute SHA-256 checksum of the downloaded file and update `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map. **Depends on: T005**.
- [ ] T004.4 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Web 2011 data. **Primary Source**: `ir_datasets.load('trec/web-track-2011')`. **Logic**: Attempt NIST fetch via `ir-datasets`. Retry with exponential backoff (base_delay=2s, multiplier=2.0, max_retries=3). If NIST still fails after retries, **raise `RuntimeError` immediately**. **DO NOT** fall back to Hugging Face, synthetic, or mock data. **Post-Fetch Step**: Compute SHA-256 checksum of the downloaded file and update `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map. **Depends on: T005**.
- [ ] T004.5 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to fetch TREC Web 2012 data. **Primary Source**: `ir_datasets.load('trec/web-track-2012')`. **Logic**: Attempt NIST fetch via `ir-datasets`. Retry with exponential backoff (base_delay=2s, multiplier=2.0, max_retries=3). If NIST still fails after retries, **raise `RuntimeError` immediately**. **DO NOT** fall back to Hugging Face, synthetic, or mock data. **Post-Fetch Step**: Compute SHA-256 checksum of the downloaded file and update `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map. **Depends on: T005**.
- [ ] T006 [P] Implement validation logic in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` to enforce schema compliance (referencing `contracts/dataset.schema.yaml`) and log warnings for zero-relevance queries. **Depends on: T004.1-T004.5, T005**.
- [X] T007 [P] Create `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/config.py` with constants for seeds, permutation counts (N=1000), batch sizes, and memory thresholds. Include: `PERMUTATION_N`, `SEED`, `BATCH_SIZE`, `MEMORY_THRESHOLD_GB` (a configurable memory limit), `RUNTIME_THRESHOLD_HOURS` (5.0), `DATA_RAW_PATH`, `RESULTS_PATH`, `ALPHA_SWEEP_START` (0.01), `ALPHA_SWEEP_END` (0.20), `ALPHA_SWEEP_STEP` (0.01).
- [X] T008 [P] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/metrics.py` functions `ndcg_at_k`, `map_at_k`, and `idcg_at_k` for NDCG@10 and MAP calculation using IDCG normalization.

**Data Integrity Verification (Depends on T004.x)**:
- [X] T039 [P] **Verification**: Implement a strict "Fail Loudly" check in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py`. **Verify that the loader contains `try/except` blocks for retry logic (as required by T004.x), but verify that the `except` block ALWAYS re-raises the `RuntimeError` and NEVER falls back to synthetic/mock data generation**. The loader MUST raise the error immediately if the verified TREC source (NIST) is unreachable after retries. **This task verifies the code in T004.x does not violate the 'no synthetic fallback' rule.** **Depends on: T004.1-T004.5**. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Permutation Test Execution (Priority: P1) 🎯 MVP

**Goal**: Execute permutation tests on TREC data to generate null distributions and p-values for NDCG@10 and MAP.

**Independent Test**: Run `main.py` with `--mode permutation` on a single query; verify `results/null_distributions/` contains CSVs and `results/p_values/` contains raw p-values.

### Test Definition for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: Tests are written first to define the expected interface and behavior. They will initially fail until the implementation stubs are created and then filled in. Stubs (function signatures) must exist before running tests.*

- [X] T010 [P] [US1] Unit test for `metrics.py` NDCG@10 calculation with known ground truth in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_metrics.py`; **Ground Truth**: `assert ndcg_at_k([1,0,0], [1,0,0]) == 1.0`; Requires presence of stub in T008
- [X] T011 [P] [US1] Unit test for permutation logic (shuffle correctness) in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_permutation.py`; Requires presence of stub in T013a
- [X] T012 [US1] Integration test: Verify p-value calculation using a rank-based estimator consistent with the reference. against a manual calculation in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/integration/test_permutation_flow.py`; Requires presence of stubs in T013a, T016

### Implementation for User Story 1

- [X] T013a [US1] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` core engine:
 1. **Step 1 (Zero-Relevance Check)**: For each query, check if relevance labels are empty. **Use the validation logic from T006**. If empty, log WARNING to `results/warnings.log` and **skip immediately** (do not enter permutation loop). **Crucially, write a record to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/config/permutation_state.json` with `query_id`, `N_actual=0`, and `status='skipped'` for these skipped queries.**
 2. Shuffle relevance labels N times per query, where **N is read from `config.PERMUTATION_N`**.
 3. **Log the ACTUAL count of permutations executed (N_actual) to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/config/permutation_state.json` in JSON format: `{"query_id": "...", "N_actual": <actual_count>, "status": "complete"}` for every query that runs. Use log level INFO.**
 4. Compute NDCG@10 and MAP for all permutations.
 5. **Depends on: T008 (metrics implementation), T006 (validation logic)**.
- [X] T013b [US1] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` runtime monitor:
 1. Integrate runtime/memory monitoring into the execution loop. Use `psutil` (memory) and `time.time()` (duration) with periodic sampling at regular intervals.
 2. Monitor `psutil.Process(os.getpid()).memory_info().rss`.
 3. **Trigger Condition**: If runtime > 5.0 hours (per FR-011) OR memory > 6 GB.
 4. **Action**: If triggered, **finalize and flush the data for all queries already processed in the current batch to disk**, then **skip remaining queries in the current batch and all subsequent batches**.
 5. **Log the specific query IDs being dropped to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/subsampling_log.csv` (with reason and timestamp)**.
 6. **Depends on: T007 (config values)**.
- [X] T013c [US1] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` subsampling handler:
 1. Ensure dropped query IDs from T013b are logged to `subsampling_log.csv`.
 2. Ensure these dropped IDs are **excluded** from T017 output (null distribution CSVs).
 3. **Depends on: T013b**.
- [X] T014 [P] [US1] Implement batch processing loop in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/permutation.py` to handle memory limits (process queries in batches, log progress). Depends on: T013a
- [ ] T017 [US1] Save null distribution CSVs to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/null_distributions/` with headers `query_id, metric, score`. **Depends on: T013a, T013c**.
- [ ] T016 [US1] Implement p-value calculation logic:
 1. **Read `permutation_state.json` generated by T013a. Iterate over each `query_id` in the file to retrieve its specific `N_actual`. This task depends on T013a for the state file.**
 2. **If `N_actual` is missing for a query, raise an error**.
 3. Calculate p-values using the formula `(r + 1) / (N_actual + 1)`, where `N_actual` is the value from the JSON state file (overriding `PERMUTATION_N` config).
 4. **If `N_actual` < `PERMUTATION_N` (and not due to subsampling), log a warning**.
 5. **Depends on: T013a (state file)**.
- [X] T018 [US1] Save raw p-values to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/p_values/raw_p_values.csv` with headers `query_id, metric, raw_p`. **Depends on: T016**.

---

## Phase 4: User Story 2 - Power Analysis & Inference Framing (Priority: P2)

**Goal**: Calculate MDES using label swapping, apply BH correction, and frame findings as associational.

**Independent Test**: Run `main.py` with `--mode power_analysis`; verify `results/mdes/` contains MDES estimates and `results/p_values/corrected_p_values.csv` exists.

### Test Definition for User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Note: Tests are written first to define the expected interface and behavior. They will initially fail until the implementation stubs are created and then filled in.*

- [X] T019 [P] [US2] Unit test for bootstrap resampling and label-swapping functions in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_power_analysis.py`; Requires presence of stub in T021
- [X] T020 [P] [US2] Unit test for Benjamini-Hochberg implementation against `statsmodels.stats.multitest` in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/unit/test_bh_correction.py`
- [ ] T025.1 [P] [US2] **Verification**: Run `tests/integration/test_mdes_stability.py` to read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` and **assert ci_width < 0.02 for BOTH NDCG@10 and MAP metrics independently**; if threshold is exceeded, **report and flag instability** but do NOT fail the build (research outcome); **Depends on: T021** (completion of T021 output file)

### Implementation for User Story 2

- [X] T021 [US2] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/power_analysis.py` MDES logic:
 1. Implement bootstrap resampling utility for power estimation.
 2. **Implement alternative hypothesis simulation by 'swapping top-k positions' in relevance labels (per spec FR-006). Note: This method overrides the Plan.md's 'noise injection' description to satisfy the higher-priority Functional Requirement FR-006.**
 3. Perform binary search over effect sizes (initial range [0.001, 0.500], tolerance ≤ 0.001 on metric delta, **max_iter=50**) to find smallest shift detectable with Power ≥ 0.8. **Effect size is defined as the delta in metric scores (NDCG or MAP), not label deltas.**
 4. **Write MDES result to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` with columns `metric, mdes, power, ci_width`**.
 **Depends on: T004.x (data loading), T008 (metrics)**.

- [X] T023 [P] [US2] Implement BH correction in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/power_analysis.py`: apply separately to NDCG and MAP p-value families (two families). **Depends on: T018** (explicitly depends on completion of T018 raw p-values)
- [ ] T026 [US2] Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/p_values/corrected_p_values.csv` with columns: `query_id, metric, raw_p, corrected_p, is_significant`. **Depends on: T023**.
- [ ] T024 [US2] Implement sensitivity analysis: **iterate (sweep) alpha values from `ALPHA_SWEEP_START` to `ALPHA_SWEEP_END` inclusive with step `ALPHA_SWEEP_STEP` as defined in config.py**. **For each adjacent pair of alpha values, compare the significance status of queries and count how many change status.** Report the count of queries where significance status changes between adjacent α values. **Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/sensitivity/alpha_sweep.csv` with columns `alpha, significant_count, status_change_count`**. **Depends on: T013a, T016, T018, T023** (completion of T023 output and raw data from T013a/T016)
- [ ] T024.1 [P] [US2] **Verification**: Run a script to read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/sensitivity/alpha_sweep.csv` and verify it exists and has the correct columns (`alpha`, `significant_count`, `status_change_count`). **Depends on: T024**.
- [ ] T027 [US2] Add explicit text generation in `main.py` output: "Findings indicate statistical association, not causal algorithmic improvement" per FR-008. **Write this text to `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/analysis_framing.txt`**.
- [ ] T027.1 [P] [US2] **Verification**: Run a script to read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/analysis_framing.txt` and verify it contains the required associational framing text. **Depends on: T027**.

---

## Phase 5: User Story 3 - Reporting & Visualization (Priority: P3)

**Goal**: Produce CSV summaries, PNG density plots, and enforce runtime/memory constraints.

**Independent Test**: Run `main.py` with `--mode report`; verify `results/plots/` contains PNGs and `results/summary.csv` exists.

### Test Definition for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test: Verify memory usage stays < 7GB during full run in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/visualization.py` to generate density plots comparing original vs. permuted scores. **Must read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/analysis_framing.txt` and include its content in the plot title or caption to satisfy FR-008. If `analysis_framing.txt` is missing, use a default fallback string: "Statistical association observed (not causal)"**.
- [ ] T030 [US3] Annotate plots with MDES and significance thresholds: **Before reading MDES, verify that `mdes_summary.csv` exists and that the `ci_width` column in the NDCG@10 row is < 0.02**. **If the CI width constraint is NOT met, use a placeholder annotation "MDES unstable (CI > 0.02)" instead of the value**. **If valid, add a vertical dashed line at `mdes` value (read from `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/mdes/mdes_summary.csv` column `mdes`) and text label "MDES={val}" to all density plots in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/plots/`; use default sans-serif font family to ensure compatibility with standard Linux runners**; **Depends: T021** (reads MDES value from T021 output)
- [ ] T031 [US3] Generate `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/summary.csv` aggregating all query-metric pairs, p-values, and MDES. **Must read `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/analysis_framing.txt` and include its content in the summary report header to satisfy FR-008. If missing, use the default fallback string.** **Depends on: T018, T023, T021** (explicitly lists all producers)
- [ ] T033 [US3] Add error handling for network failures in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/data_loader.py` (graceful exit with error code)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Update `README.md` with sections: 'Installation', 'Usage', 'Output Artifacts'
- [ ] T035 Code cleanup: Remove debug prints and ensure logging levels are appropriate
- [ ] T036 Performance optimization: Verify batch processing logic is efficient; **Ensure memory < 6GB during batch of 50 queries**
- [ ] T037 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly
- [ ] T038 [US3] Add content checksums to `data/raw/`, `data/processed/`, and `results/` artifacts for reproducibility (Constitution Principle V); **Mechanism**: Implement a script to **read all files in `projects/PROJ-362-evaluating-the-statistical-validity-of-c/data/raw/`, `projects/PROJ-362-evaluating-the-statistical-validity-of-c/data/processed/`, and `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/`, sort the list of all discovered files by their full relative path string in ascending ASCII order, compute SHA-256 hash for each, and append the results to `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` in the `artifact_hashes` map (flat structure: `artifact_hashes: { relative_path: sha256_hash }`). **CRITICAL**: If `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` does not exist, create it with the proper YAML structure (`artifact_hashes: {}`) before writing hashes.**; **Depends on: T017, T018, T021, T023, T026, T031** (completion of all artifact generation tasks - **Note: T038 depends directly on artifact generation, NOT on T030 Visualization, to avoid blocking if visualization fails**)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 7)**: Can run in parallel with Phase 2/3 but must be complete before final integration testing.

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

*The following clarifies the Test-Driven Development (TDD) flow for the tasks listed above:*

1. **Define Tests First**: Tasks T010-T012 (Tests) are listed before T013a-T018 (Implementation) to reflect that test cases are defined first based on requirements.
2. **Create Interface Stubs**: Before running the tests, minimal interface stubs (function signatures, empty classes) must be created in the implementation files (T013a-T018). This allows the test runner to execute the tests, which will **FAIL** because the logic is not yet implemented.
3. **Run Tests to Fail**: Execute T010-T012. They should fail due to missing implementation logic (asserting that the stubs exist but the logic is empty).
4. **Implement Logic**: Fill in the logic in T013a-T018 to make the tests pass.
5. **Verify Pass**: Re-run T010-T012 to confirm they now pass.

*This ensures the 'Tests First' TDD cycle: Red (Tests Fail) -> Green (Tests Pass) -> Refactor.*

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on a limited number of CPU cores, a constrained amount of RAM, and without GPU acceleration. Avoid any heavy model loading or 8-bit quantization.
- **Data Integrity**: All data must come from verified TREC sources (NIST primary only). No synthetic data generation for input metrics. **T039 ensures strict adherence to this by forbidding synthetic fallbacks while allowing verified NIST retry logic.**
- **State Management**: The file `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` is a required project artifact for Constitution Principle V. It must be created if missing by the checksumming task (T038).