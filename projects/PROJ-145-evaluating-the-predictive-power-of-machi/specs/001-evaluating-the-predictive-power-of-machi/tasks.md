# Tasks: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

**Input**: Design documents from `/specs/001-evaluating-the-predictive-power-of-machi/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY as defined by the Spec's "Independent Test" sections.

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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root directories: `code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`
- [ ] T001b [P] Create empty `__init__.py` files in all new directories to initialize Python packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `code/config.py` with hyperparameters, random seeds (arbitrary), and path constants
- [X] T002a [P] [US1] **Config Definitions**: Add `N_NOVEL_SAMPLES = 1000 `, `ELEMENT_SUBSET = ["Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Al"] ` to `code/config.py`. **Requirement**: Define the constant and a concrete subset of transition/post-transition metals to sample from.
- [X] T003 [P] Initialize a Python project using a recent, stable version of the language. with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, scipy, datasets, matplotlib, seaborn, pytest)
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `code/__init__.py` and package structure
- [ ] T006 [P] Setup `tests/` directory structure (unit, integration)
- [X] T007 [P] Configure basic logging infrastructure in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Novel Composition Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest HEA thermodynamic data from "Materials Project API and AFLOWlib" (live implementation), generate `heas_train.csv`, `holdout_known.csv`, and `true_novel.csv` with strict separation and verification.

**Independent Test**: Verify `heas_train.csv` contains only known entries, `holdout_known.csv` entries exist in source but not training, and `true_novel.csv` entries return "Not Found" against the live source APIs.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T019b [P] [US1] **Verification of Fail-Loudly**: Add a unit test in `tests/unit/test_ingestion.py` that verifies `code/data_ingestion.py` raises an exception when the dataset fetch is simulated to fail, ensuring no synthetic fallback logic exists. **Logic**: Mock the `datasets.load_dataset` call to raise an error; assert the script exits with a non-zero code and no synthetic data is generated. **Dependency**: Requires T012 (Data Ingestion) skeleton to exist. **Ordering**: Must be written before T012 implementation.
- [X] T010 [P] [US1] Unit test for data filtering logic in `tests/unit/test_ingestion.py` (verify + element filter)
- [X] T011 [P] [US1] Integration test for dataset split logic in `tests/integration/test_split.py` (verify no overlap between train/holdout/novel)

### Implementation for User Story 1

- [ ] T017a [US1] **Download Raw Data**: Download the raw `hmao` dataset to `data/raw/` using `datasets.load_dataset(..., streaming=True)`. **Output**: `data/raw/hmao_raw.parquet` (or equivalent). **Constraint**: Must use `streaming=True` to respect RAM limits. **External Checksum**: Retrieve the known SHA256 checksum from the HuggingFace dataset metadata (not from the local file) to use for integrity verification.
- [ ] T017b [US1] **Compute Checksum & Update Config**: Compute the SHA256 checksum of `data/raw/hmao_raw.parquet`. Compare it against the *known external* checksum retrieved in T017a. If they match, update `code/config.py` to set `EXPECTED_HMAO_CHECKSUM` for future runs. **Output**: Updated `code/config.py`. **Dependency**: T017a.
- [ ] T017c [US1] **Live API Client Implementation**: Implement `code/api_client.py` to query the "Materials Project" and "AFLOW" APIs (or their public mirrors) for composition existence. **Logic**: 1. Accept a composition string. 2. Query the API with exponential backoff (max 3 retries). 3. Return `{"status": "Found", "data":...}` or `{"status": "Not Found"}`. **Constraint**: Must handle rate limits and timeouts. **Output**: A callable `query_live_api(composition_string)` function. **Dependency**: T003 (requirements).
- [ ] T016 [US1] **Streaming Integrity Check**: Implement streaming integrity check in `code/data_ingestion.py`: Validate the dataset checksum against `config.EXPECTED_HMAO_CHECKSUM` (defined in T017b) and implement **exponential backoff with a maximum of 3 retries** if the fetch fails (per Spec Edge Case 1). Do NOT use mock logging. **Dependency**: T017b.
- [ ] T012 [US1] **Data Ingestion Implementation**: Implement `code/data_ingestion.py` to load `hmao/all_apis_for_multiapi` using `datasets.load_dataset(..., streaming=True)`. **Mapping**: `formation_energy_per_atom` -> `target_energy`, `mixing_enthalpy` -> `target_hmix`. Filter for multi-element systems (systems with multiple elements). **Constraint**: Use the live API client (T017c) for any verification steps. **Fail-Loudly Rule**: The script MUST raise a `ConnectionError` or `ValueError` immediately if the dataset fetch fails; NO synthetic data generation or fallback logic is permitted.
- [ ] T019c [US1] **Strict Composition Comparison**: Implement strict composition string comparison check to prevent hash collisions in `code/data_ingestion.py`. **Output**: Produce a `deduplicated composition index` artifact (set of strings) consumed by T014b, T014c, and T015. **Dependency**: T012.
- [ ] T014a [US1] **Exclusion Logic Implementation**: Implement logic in `code/data_ingestion.py` to identify element pairs with the highest co-occurrence in the *loaded* training set (from T012) and define them as exclusion criteria. **Algorithm**: Calculate co-occurrence frequency for all pairs; exclude the top N pairs where N is configurable. **Output**: A list of tuples in `code/config.py` as `EXCLUSION_PAIRS`. **Dependency**: T012. **Constraint**: Do NOT hardcode specific pairs; derive dynamically.
- [ ] T014b [US1] **Hold-out Known Sampling**: Sample `config.N_NOVEL_SAMPLES` unique combinations of the excluded subset, ensuring each combination contains a small, fixed number of elements (compositions containing `EXCLUSION_PAIRS` from T014a). **Algorithm**: Iterate all 5-element subsets of the periodic table, filter by exclusion criteria. **Output**: A list of candidate compositions. **Dependency**: T014a.
- [ ] T014c [US1] **Hold-out Known Verification**: Verify the candidates from T014b exist in the "Source API" by invoking `query_live_api` (from T017c) and confirming a "Found" status, while ensuring they are NOT in `heas_train.csv`. **Output**: `data/processed/holdout_known.csv`. **Dependency**: T014b, T017c.
- [ ] T014d [US1] **Hold-out Known Export**: Export the verified hold-out set to `data/processed/holdout_known.csv`. **Dependency**: T014c.
- [ ] T015 [US1] **True Novel Generation**: Sample `config.N_NOVEL_SAMPLES` unique 5-element combinations from `config.ELEMENT_SUBSET` (defined in T002a) using `itertools.combinations` and a fixed random seed (42). Filter for those NOT present in `heas_train.csv` AND NOT present in the "Source API" by invoking `query_live_api` (from T017c) and confirming a "Not Found" status. Export to `data/processed/true_novel.csv`. **Constraint**: Must use a fixed random seed for reproducibility. **Dependency**: T017c, T019c.
- [ ] T018a [US1] **Source API Query Simulation (Deprecated)**: *This task is deprecated in favor of T017c. Do not implement.*
- [ ] T018b [US1] **Validation Script**: Add validation script `code/validate_splits.py` to verify disjoint sets and live API existence for holdout/novel sets. **Logic**: Assert `len(set(train) & set(holdout)) == 0`, `len(set(train) & set(novel)) == 0`, and `len(set(holdout) & set(novel)) == 0`. Verify `holdout` entries exist in the live API and `novel` entries do not. **Output**: Exit code 0 if valid, 1 otherwise; log counts to stdout. **Dependency**: T017c, T014d, T015.
- [ ] T018c [US1] **API Fallback/Proxy Mapping**: Create `code/api_mapping.md` explicitly documenting the mapping of FR-002 "Source API" requirement to the live API implementation in T017c. **Required Sections**: 1. FR-002 Requirement, 2. Live API Implementation (T017c), 3. Fallback Strategy (if any), 4. Traceability Matrix. **Verification**: Run a diff check against the source text in `plan.md` if quoting. **Dependency**: T017c.
- [ ] T019a [US1] **Documentation**: Create `docs/api_deviation.md` explicitly documenting the deviation from live "Materials Project/AFLOW API" verification to static `hmao` proxy verification for CI reproducibility (if applicable). **Required Sections**: 1. Proxy Hash (SHA256 of `hmao` snapshot), 2. Justification (lack of live API access), 3. Constitution Reference (Principle I & III), 4. Limitation Statement (verification is against a subset, not the full live API), 5. Traceability (explicitly map T018a logic to FR-002 "Source API" requirement). **Content Requirement**: Explicitly quote the "Dataset Strategy Note" section from `plan.md` regarding the use of the `hmao` proxy. Reference FR-001, US-1, **Plan: Dataset Strategy Note**, and **Constitution Principle I**. Explicitly state that the `hmao` proxy acts as the "Source API" for FR-002 and US-1 Acceptance 3. **Verification**: Verify the quoted text matches the source in `plan.md` exactly via a diff check. **Dependency**: T018c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

**Goal**: Compute compositional descriptors via `pymatgen` and train Random Forest/Gradient Boosting models with k-fold cross-validation

**Independent Test**: Verify 5-fold CV $R^2$ is calculated, model artifacts (`.pkl`) are generated, and execution completes within 6 hours on CPU without GPU errors.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T019 [P] [US2] Unit test for descriptor calculation in `tests/unit/test_descriptors.py` (verify weighted mean/variance for radius, electronegativity, VEC, melting point)
- [ ] T020 [P] [US2] Unit test for numerical stability in `tests/unit/test_descriptors.py` (verify clamping of near-zero values to a small positive constant)

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/feature_engineering.py` to calculate weighted mean and variance descriptors (atomic radius, electronegativity, VEC, melting point) using `pymatgen` for all datasets. **Output**: `data/processed/heas_train_features.csv` with columns: `mean_atomic_radius`, `var_atomic_radius`, `mean_electronegativity`, `var_electronegativity`, `mean_VEC`, `var_VEC`, `mean_melting_point`, `var_melting_point`.
- [ ] T022 [US2] Implement numerical clamping logic (min threshold) in `code/feature_engineering.py` to prevent division errors.
- [ ] T023 [US2] Implement `code/train_models.py` to train `RandomForestRegressor` and `GradientBoostingRegressor` with k-fold cross-validation.
- [ ] T024 [US2] Implement hyperparameter tuning (max_depth, n_estimators) within `code/train_models.py`.
- [ ] T025 [US2] Implement model saving logic in `code/train_models.py` to output `.pkl` artifacts to `data/models/`.
- [ ] T026 [US2] Add logging for training metrics (mean $R^2$) and execution time in `code/train_models.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Extrapolation Evaluation and Uncertainty Analysis (Priority: P3)

**Goal**: Evaluate models on "Hold-out Known" (error) and "True Novel" (uncertainty) sets, perform statistical tests, and generate final report.

**Independent Test**: Compare $R^2$ on holdout vs training, verify ensemble variance correlates with convex hull distance, and generate ranked candidate report.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T027 [P] [US3] Integration test for evaluation pipeline in `tests/integration/test_evaluation.py` (verify permutation test and Spearman correlation outputs)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/evaluate.py` to load trained models and predict on `holdout_known.csv`.
- [ ] T029 [US3] Implement $R^2$ and MAE calculation for `holdout_known.csv` in `code/evaluate.py` and compare to training $R^2$.
- [ ] T030 [US3] Implement prediction on `true_novel.csv` in `code/evaluate.py` with ensemble variance calculation.
- [ ] T031 [US3] **Convex Hull Distance**: Implement distance calculation for `true_novel.csv` entries in `code/evaluate.py`. **Algorithm**: Use `scipy.spatial.ConvexHull` on the *training set's* descriptor space, specifically using the 8 columns generated by T021: `mean_atomic_radius`, `var_atomic_radius`, `mean_electronegativity`, `var_electronegativity`, `mean_VEC`, `var_VEC`, `mean_melting_point`, `var_melting_point`. For each novel point, compute the Euclidean distance to the nearest facet of the hull. If the point is inside the hull, distance = 0. **Output**: `distance_to_hull` column in the prediction results.
- [ ] T032 [US3] **Statistical Test (Permutation)**: Implement a **Permutation Test** to compare error distributions of training vs. holdout sets in `code/evaluate.py` (satisfying FR-006). **Logic**: 1. **Check if ground truth is available** for the `holdout_known` set. If NOT, log a skip and exit. 2. If available, calculate the observed difference in mean absolute error (MAE) between training and holdout sets. 3. Pool the errors from both sets. 4. Randomly shuffle the pooled errors and re-split into two groups of the original sizes. 5. Calculate the mean difference for the shuffled groups. 6. Repeat the procedure a sufficient number of times to ensure stable estimation. 7. Calculate p-value as the proportion of shuffled differences >= observed difference. **Output**: p-value. **Constraint**: If the dataset size is insufficient for the permutation test (e.g., < 10 samples in either set), raise a `ValueError` with a clear message; do NOT fall back to a t-test or other method.
- [ ] T033 [US3] **Correlation**: Implement Spearman rank correlation test (FR-007) between variance (from T030) and convex hull distance (from T031) in `code/evaluate.py`. **Note**: This metric replaces the Plan's "Perturbation Magnitude" to satisfy Spec FR-005/FR-007, measuring geometric extrapolation distance rather than sensitivity to perturbation. **Output**: Spearman coefficient and p-value.
- [ ] T035b [US3] **Statistical Robustness Check**: Ensure `code/evaluate.py` explicitly handles the case where `true_novel` set is empty or too small (< 10 samples) for statistical correlation by raising a `ValueError` with a clear message, rather than returning `NaN` or skipping the test silently.
- [ ] T035a [US3] **Threshold Calculation**: Compute a lower percentile of the *training set's* variance distribution to assess the distribution's tail behavior.. **Algorithm**: Train multiple independent Random Forest models on the full training set using distinct random seeds.. For each sample in the training set, collect the 10 predictions and calculate the variance. Calculate the 10th percentile of this distribution. **Output**: A single float value (threshold) to be used by T034.
- [ ] T034a [US3] **Candidate Filtering & Ranking**: Implement logic in `code/report.py` to filter candidates where variance <= threshold (from T035a). Sort by `prediction_variance` ASC, then by `distance_to_hull` ASC. Select a representative subset. **Output**: Intermediate list of candidates.
- [ ] T034b [US3] **CSV Generation**: Generate `data/processed/top_novel_candidates.csv`

The specific value to remove/generalize: 'a set of'

Rewritten passage:
Generate `data/processed/top_novel_candidates.csv` with columns: `composition_string`, `predicted_energy`, `variance`, `distance_to_hull`, `rank` from the filtered list in T034a.
- [ ] T034c [US3] **JSON Summary Generation**: Generate `data/processed/variance_distribution_summary.json` containing histogram data for the variance distribution relative to the 10th percentile to satisfy SC-005.
- [ ] T034d [US3] **Report Assembly**: Implement final report generation in `code/report.py`. **Logic**: Include statistical summary, correlation coefficient from T033, and DFT status from T041. **Requirement**: If `data/processed/dft_validation_status.txt` indicates failure, explicitly include the statement "The uncertainty metric for 'True Novel' candidates is an unvalidated assumption" in the final report summary. **Dependency**: T034a, T034b, T034c, T041.
- [ ] T041 [US3] **DFT Attempt**: Implement `code/dft_attempt.py` to attempt DFT calculation on the top novel candidates (from T034a). **Stack**: Use Quantum ESPRESSO (open-source, reproducible) via the provided container or script. **Logic**: 1. Generate input files (POTCAR, KPOINTS, etc.) for the top 5 candidates. 2. Submit job with a timeout appropriate for the task duration (e.g., an hour per job). 3. Parse output for formation energy. 4. If successful, write `data/processed/dft_results.csv`. 5. If it fails (time/resource), write `data/processed/dft_validation_status.txt` containing the exact string "DFT attempt failed due to time/resource constraints; uncertainty metric is an unvalidated assumption". **Constraint**: Must define a concrete workflow; no stubs. **Dependency**: T034a.
- [ ] T042 [US3] **Unvalidated Statement**: Ensure `code/report.py` explicitly includes the statement "The uncertainty metric for 'True Novel' candidates is an unvalidated assumption" in the final report summary if `data/processed/dft_validation_status.txt` indicates failure, satisfying FR-009.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` with installation steps and data flow diagram
- [ ] T037 Refactor code to remove unused imports and ensure PEP8 compliance
- [ ] T038 Profile `code/data_ingestion.py` and optimize streaming logic to ensure <7GB RAM usage
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Run quickstart.md validation

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces** `heas_train.csv`, `holdout_known.csv`, `true_novel.csv`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Depends on** US1 outputs (`heas_train.csv`). **Produces** trained models.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Depends on** US1 outputs (test sets) and US2 outputs (models). **Produces** evaluation metrics and final report.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading/filtering before feature engineering
- Feature engineering before model training
- Model training before evaluation
- Evaluation before report generation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for data filtering logic in tests/unit/test_ingestion.py"
Task: "Integration test for dataset split logic in tests/integration/test_split.py"

# Launch all implementation tasks for User Story 1:
Task: "Download raw data (T017a)"
Task: "Compute checksum (T017b)"
Task: "Implement data ingestion (T012)"
Task: "Implement live API client (T017c)"
Task: "Implement exclusion logic (T014a)"
Task: "Implement hold-out sampling (T014b)"
Task: "Implement hold-out verification (T014c)"
Task: "Implement true novel generation (T015)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Splitting)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify disjoint sets and data integrity)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained)
4. Add User Story 3 → Test independently → Deploy/Demo (Evaluation complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Feature Engineering & Training) - *Can start once US1 data is available or mocked for local dev*
 - Developer C: User Story 3 (Evaluation) - *Can start once US1 & US2 outputs are available*
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
- **Critical**: Ensure `code/data_ingestion.py` uses `streaming=True` for `hmao/all_apis_for_multiapi` to respect RAM constraints.
- **Critical**: Ensure `code/data_ingestion.py` samples exactly `config.N_NOVEL_SAMPLES` combinations (T014, T015) instead of hardcoding a count.
- **Critical**: Ensure `code/feature_engineering.py` clamps near-zero values to a small positive constant to prevent numerical instability.
- **Critical**: Ensure `code/evaluate.py` performs strict composition string comparison to avoid hash collisions.
- **Critical**: Ensure `code/report.py` filters candidates by the 10th percentile variance threshold (T035a) before ranking (T034).
- **Critical**: The "Source API" for novelty verification is now the **live API** implementation (T017c), not a static proxy. T018c documents the mapping.
- **Critical**: The sampling strategy for "True Novel" (T015) must explicitly iterate through the generated combinations and verify their absence in the live API via a fast lookup structure (e.g., a pre-computed set of composition strings from T017c) to avoid false positives.
- **Critical**: The convex hull distance calculation (T031) must use `scipy.spatial.ConvexHull` on the training set's descriptor space (specifically the 8 columns generated by T021) and compute the distance of novel points to the nearest facet or vertex, handling points inside the hull correctly (distance = 0).
- **Critical**: The permutation test (T032) and Spearman correlation (T033) must handle edge cases where the dataset size is small or variances are zero, potentially using `scipy.stats.permutation_test` and `scipy.stats.spearmanr` with `nan_policy='omit'`.
- **Critical**: The final report (T034) must include a disclaimer about the limitations of the "True Novel" set being generated synthetically via sampling rather than discovered via a global search, and explicitly state the sample size and seed used.
- **Critical**: T035a must calculate the 10th percentile deterministically (10 models, seeds 0-9) and pass it to T034 without intermediate files to ensure reproducibility.
- **Critical**: **Data Integrity**: T012 and T019b must ensure the loader fails loudly on fetch errors. No synthetic fallbacks are permitted.
- **Critical**: **Statistical Robustness**: T035b must ensure statistical tests fail loudly if input data is insufficient, rather than returning silent `NaN` values.
- **Critical**: **Exclusion Logic**: T014a must derive exclusion pairs dynamically from the loaded training data (co-occurrence analysis) rather than hardcoding specific pairs.
- **Critical**: **Metric Alignment**: T031 and T033 must use Convex Hull Distance as per Spec FR-005, overriding the Plan's "Perturbation Magnitude" to satisfy the Spec's explicit requirement.
- **Critical**: **DFT Validation**: T041 and T042 must ensure that if DFT fails, the report explicitly states the uncertainty metric is an unvalidated assumption. T041 must use a concrete DFT stack (Quantum ESPRESSO) and generate actual input files.
- **Critical**: **API Simulation**: T017c (Live API) must be implemented and invoked by T014c and T015 to satisfy the Spec's requirement for "Source API" verification. T018c documents the mapping.
- **Critical**: **Task Ordering**: All tasks are now ordered to respect data dependencies (Producers before Consumers). T017a/T017b/T017c precede T012/T016. T019c precedes T014/T015. T014a precedes T014b. T012 precedes T014a.