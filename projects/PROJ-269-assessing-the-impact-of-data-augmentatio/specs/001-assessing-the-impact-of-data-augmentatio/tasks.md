# Tasks: Assessing the Impact of Data Augmentation on Statistical Power in Small Samples

**Input**: Design documents from `/specs/001-assess-augmentation-impact/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directories `code/` and `tests/` at repository root.
- [ ] T001b [P] Create project directories `data/raw/`, `data/derived/`, `results/`, and `contracts/` at repository root.
- [ ] T001c [P] Create `projects/PROJ-269-assessing-the-impact-of-data-augmentatio/requirements.txt` with pinned versions: pandas, numpy, scikit-learn, imbalanced-learn, scipy, requests, pytest.
- [X] T001d [P] Create `projects/PROJ-269-assessing-the-impact-of-data-augmentatio/code/__init__.py` and `tests/__init__.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes feasibility gates.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/download_data.py`: Fetch verified UCI datasets (Breast Cancer, Ionosphere, Heart Disease) via **single canonical URLs** and their expected SHA256 checksums. Save to `data/raw/`. **Constraint**: If the fetched count does not meet the specification requirement, log a warning to `data/derived/fetch_count.log` for agent processing. **Do NOT write to state files**; the Advancement-Evaluator Agent handles state updates.
- [X] T004b [P] Implement deviation recording logic in `code/main.py`: Create logic to dynamically adapt the simulation loop to the variable dataset count (3 vs 5). **Dependency**: T004. **Note**: This task does not write artifacts; it only adapts logic.
- [X] T004c [P] Implement logging and checksum logic: Write the specific deviation count to `data/derived/deviation_log.json`. Compute the SHA256 checksum of this file and append the hash to the state manifest record for agent ingestion. **Dependency**: T004b.
- [X] T005 [P] Implement `code/subsample.py`: Create stratified subsampling function for N=15, 25, 40. **Target Column Detection**: Look for 'target', then 'class', then 'label', then default to the last column. **Edge Cases**: If class count < 5 for a configuration, first attempt to reduce N (e.g., N=15 -> N=10) to preserve the configuration; if reduction fails (N < 5), skip the configuration, log a warning, and append details to `data/derived/skipped_configurations.log`.
- [X] T006 [P] Implement `code/augment.py`: Create functions for Gaussian noise injection, SMOTE, and Random Oversampling using `imbalanced-learn`; ensure no CUDA/GPU dependencies; handle zero-variance samples.
- [X] T008a [P] Define JSON schema for simulation output: Create `contracts/simulation_schema.json` defining the structure for p-value distributions, error rates, and metadata. **Must be valid JSON and exist before T007 runs.** (Note: T007 execution is blocked until this task is complete).
- [X] T034 [P] Validate computational runtime: Implement a validation script in `code/validation.py` to run a sample configuration (1 dataset, 1 size) and verify the runtime is within the **6-hour limit** (SC-004). This task is a blocking prerequisite for T007.
- [X] T035 [P] Verify memory usage: Implement a validation script in `code/validation.py` to run a sample configuration and verify memory usage (process memory RSS) remains under **7 GB** (SC-005). This task is a blocking prerequisite for T007.
- [X] T007 [P] Implement `code/simulation.py` **Infrastructure**: Create the generic Monte Carlo loop infrastructure (configuration management, random seed pinning, iteration loop) to run **[deferred] iterations** per configuration as mandated by FR-004. **Do NOT implement ground truth logic here**; implement only the loop mechanics. **Dependency**: Requires T008a, T034, T035.
- [X] T008b [P] Implement `code/analyze.py`: Implement error rate calculation (Type I/II), KS test wrapper (p-value distributions only), and JSON reporting structure. **Dependency**: Requires T007 output.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Error Rate Estimation (Priority: P1) 🎯 MVP

**Goal**: Establish ground-truth baseline for Type I and Type II error rates using original, non-augmented small-sample datasets.

**Independent Test**: Run simulation on original subsampled datasets (N=15, 25, 40) without augmentation and verify output includes calculated empirical error rates and confidence intervals.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for stratified subsampling logic in `tests/test_subsample.py` (verify class ratio preservation)
- [X] T010 [P] [US1] Integration test for baseline simulation loop in `tests/test_simulation.py` (verify p-value distribution generation)

### Implementation for User Story 1

- [X] T014 [US1] Implement Ground Truth Experimental Conditions in `code/simulation.py`: Create helper functions for (1) label permutation (shuffle all labels using pinned seed) for Type I error and (2) mean shift (Cohen's d = 0.5) for Type II error. **These functions are for Augmented/Ground Truth scenarios, not the Baseline.**
- [X] T013 [US1] Implement Baseline Monte Carlo loop in `code/simulation.py`: Use T007 infrastructure to run [deferred] iterations on **original, non-augmented** data. **Logic**: Do NOT apply label permutation or mean shift here; this is the pure baseline. **Dependency**: Requires T007 infrastructure and T014 helper functions to ensure the helper functions exist for the simulation infrastructure, even if not invoked in this specific baseline branch.
- [X] T015 [US1] Write code to save baseline results to `results/[dataset]_[size]_baseline_null.json` and `results/[dataset]_[size]_baseline_alt.json`. **Iteration Logic**: Iterate over the **verified datasets available** (breast_cancer, ionosphere, heart_disease) and sizes [15, 25, 40] as per the Plan's deviation from the Spec's 5 datasets. **Naming convention**: `[dataset]` = lowercase underscore (e.g., 'breast_cancer'), `[size]` = integer (e.g., '15').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Augmentation Technique Simulation (Priority: P2)

**Goal**: Apply Gaussian noise, SMOTE, and Random Oversampling to subsampled datasets and re-run hypothesis tests.

**Independent Test**: Apply SMOTE to a specific dataset configuration and verify output includes transformed dataset and resulting p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for SMOTE edge case handling (zero variance samples) in `tests/test_augment.py`
- [X] T017 [P] [US2] Unit test for Gaussian noise injection parameters in `tests/test_augment.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement Gaussian noise injection in `code/augment.py` with configurable standard deviation (default a small positive threshold). **Edge Case Logic**: If zero-variance samples are generated, **detect and exclude them**; if the resulting sample size is < 5, **reduce N** or skip the iteration.
- [X] T019 [P] [US2] Implement SMOTE augmentation in `code/augment.py` with edge case handling. **Edge Case Logic**: If N < 5 or extreme imbalance prevents SMOTE, **reduce N** or skip the configuration as per FR-002.
- [X] T020 [P] [US2] Implement Random Oversampling in `code/augment.py`. **Edge Case Logic**: If zero-variance samples are generated, **detect and exclude them**; if the resulting sample size is < 5, **reduce N** or skip.
- [X] T021 [US2] Integrate augmentation functions into `code/simulation.py` Monte Carlo loop (separate branches for Null and Alt conditions). **Requires T013 (baseline loop), T014 (ground truth logic), and T018-T020 completion.** Note: Phase 3 must complete before Phase 4 integration tasks can begin.
- [X] T023 [US2] Write code to save augmented results to `results/[dataset]_[size]_[method]_null.json` and `results/[dataset]_[size]_[method]_alt.json`. **Mandatory**: Distinct files for Null and Alt conditions for each method.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Threshold Identification (Priority: P3)

**Goal**: Compare empirical error rates between baseline and augmented groups, identify unsafe thresholds, and generate final report.

**Independent Test**: Process results for all configurations and verify summary report lists measured error rates, differences, and fixed design threshold (0.10).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Integration test for comparative analysis logic in `tests/test_analysis.py`
- [X] T025 [P] [US3] Contract test for final JSON output schema in `tests/contract/test_results_schema.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement KS test wrapper in `code/analyze.py` for supplementary distributional shift diagnostics: **Apply ONLY to p-value distributions** (FR-006). **Constraint**: Input validation must reject any input that is not a list/array of p-values.
- [X] T027 [US3] Implement comparative analysis logic: Calculate difference in Type I/II error rates between baseline and each augmentation method.
- [X] T028 [US3] Implement threshold identification logic: Flag configurations where Type I error > 0.10 **AND** compare against baseline error rate to quantify impact (FR-005).
- [X] T029 [US3] Implement final report generation in `code/analyze.py`: Aggregate results, compute power (1 - Type II), and format output. **Mandatory**: Include fixed design threshold (0.10) value in JSON output (SC-001).
- [X] T031 [US3] Create `code/main.py` orchestration script to run full pipeline: Download → Subsample → Baseline → Augment → Analyze → Report. **Must be last task in Phase 5.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Post-Processing & Reporting

**Purpose**: Finalizing artifacts and ensuring compliance

- [ ] T030 [US3] Inject "DISCLAIMER: Findings are associational..." string into **every** result JSON file (baseline and all augmented variants) and summary report as per FR-007. **Mechanism**: Use glob pattern `results/**/*.json` to discover all files. **Structure**: Ensure the JSON has a `metadata` object; if not, create it; then set `metadata.disclaimer` to the string. **Post-Processing**: Compute SHA256 of the modified file and append the hash to the state manifest. **Dependency**: Requires T015, T023, and T029 completion.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Add comprehensive docstrings and type hints to `code/download_data.py`, `code/subsample.py`, `code/augment.py`, `code/simulation.py`, `code/analyze.py`, `code/main.py` to pass pydocstyle checks with the project's `.pydocstyle` config.
- [ ] T032b [P] Add `pytest` fixtures for dataset loading and random seed management in `tests/conftest.py`.
- [ ] T036 [P] Update `quickstart.md` with instructions for running the full study.
- [ ] T037 [P] Generate `data-model.md` documenting `Dataset Configuration` (attrs: source, size, aug_type), `Simulation Run` (attrs: seed, p_value, timestamp), and `Error Rate Profile` (attrs: type_i_rate, type_ii_rate, ci_bounds) entities using Mermaid ERD format.

---

## Phase R: Revision & Compliance (Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, reproducibility, and edge-case handling.

- [X] T038 [US1] Implement robust URL validation in `code/download_data.py`: Create a `VERIFIED_DATASETS` constant mapping dataset names to **single canonical URLs** and their expected SHA256 checksums. **Constraint**: If the fetched file does not match the checksum, raise a `DataFetchError` and **never** fall back to synthetic data (per Constitution Rule: "The loader must FAIL LOUDLY").
- [X] T039 [US1] Add deterministic seed verification task: Implement a unit test in `tests/test_simulation.py` that runs the baseline loop twice with the same seed and asserts that the resulting p-value distributions are bitwise identical (within floating point tolerance) to ensure strict reproducibility.
- [ ] T040 [US2] Enhance SMOTE edge-case logging in `code/augment.py`: When SMOTE is skipped due to N < 5 or extreme imbalance, log the specific dataset name, sample size, and class distribution to `data/derived/skipped_configurations.log` with a structured JSON format for later aggregation.
- [X] T041 [US3] Implement "Safety Threshold" sensitivity analysis: Add a task in `code/analyze.py` to re-run the comparative analysis with alternative thresholds to demonstrate the robustness of the "unsafe" classification near the 0.10 boundary.
- [ ] T042 [US3] Add "Computational Cost" metric to final report: Extend `code/analyze.py` to calculate and record the average runtime per iteration for each augmentation method., ensuring the final report addresses SC-004 explicitly with empirical data.
- [X] **Resolved**: Task T022 (zero-variance sample removal) was listed in a previous "REJECTED" list but is fully covered by T018, T019, and T020. T022 has been removed to eliminate redundancy.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Post-Processing (Phase 6)**: Depends on all User Stories being complete
- **Revision (Phase R)**: Can be implemented in parallel with Phase 5 or 6, but must be complete before final release
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (logic before orchestration)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different augmentation techniques (T018, T019, T020) can be implemented in parallel
- Revision tasks (T038-T042) can be implemented in parallel with Phase 5/6 tasks as they focus on specific code paths

---

## Parallel Example: User Story 2

```bash
# Launch augmentation implementations in parallel:
Task: "Implement Gaussian noise injection in code/augment.py"
Task: "Implement SMOTE augmentation in code/augment.py"
Task: "Implement Random Oversampling in code/augment.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Baseline only)
4. **STOP and VALIDATE**: Test baseline error rates against theoretical expectations
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Baseline) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Augmentation) → Test independently → Deploy/Demo
4. Add User Story 3 (Analysis) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline logic)
 - Developer B: User Story 2 (Augmentation techniques)
 - Developer C: User Story 3 (Analysis and reporting)
3. Stories complete and integrate in `main.py`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: Ensure all tasks run on CPU-only CI (no 8-bit quantization, no CUDA, no large models). Use `imbalanced-learn` CPU mode and small sample sizes only.
- **Target Column Priority**: 'target' > 'class' > 'label' > last column (used in T005, T013).
- **Schema Dependency**: T007 requires T008a (schema) to exist before execution.
- **Log File**: Skipped configurations are logged to `data/derived/skipped_configurations.log`.
- **Feasibility Gates**: T034 and T035 are mandatory blocking prerequisites for the simulation loop.
- **Deviation Handling**: T004, T004b, and T004c handle the 3 vs 5 dataset deviation explicitly.
- **Revision Concerns**: T038-T042 address specific reviewer concerns regarding data integrity, reproducibility, and edge-case handling.
- **Resolved**: T022 was superseded by T018-T020 and removed.