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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Project Initialization**: Create root directories (`code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`) using `mkdir -p`. Initialize Python packages with `__init__.py` in each. Install dependencies from `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, scipy, datasets, matplotlib, seaborn, pytest). Configure linting (ruff) and formatting (black) by creating `.ruff.toml` and `pyproject.toml` with standard settings. **Output**: Verified directory structure and functional `venv`. **Dependency**: None.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] **Config Definitions**: Create `code/config.py` with hyperparameters, random seeds (e.g., `RANDOM_SEED = 42`), and path constants. Define `EXPECTED_AFLOW_CHECKSUM` as a static string constant (to be populated with the known SHA256 hash from the HuggingFace dataset metadata). **Do NOT** define a hardcoded `ELEMENT_SUBSET`; instead, define `ELEMENT_SOURCE_LIST` as a broad list of transition and post-transition metals (e.g., Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Y, Zr, Nb, Mo, Tc, Ru, Rh, Pd, Ag, Cd, Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg, Al, Si, P, S, Cl, K, Ca, Ga, Ge, As, Se, Br, Rb, Sr, In, Sn, Sb, Te, I, Cs, Ba, La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu) to be combined with elements found in the dataset. **Output**: `code/config.py`.
- [X] T003 [P] **Package Structure**: Implement `code/__init__.py` and ensure `tests/__init__.py` exists. **Output**: Valid Python package structure.
- [X] T004 [P] **Logging Infrastructure**: Configure basic logging in `code/config.py` to output to `code/logs/app.log` with rotating file handler. **Output**: `code/config.py` updated.
- [X] T005 [P] **Test Infrastructure**: Setup `tests/` directory structure (unit, integration) with `__init__.py` files. **Output**: `tests/unit/`, `tests/integration/`.
- [X] T038 [P] **Profiling & RAM Constraint Check**: Implement a profiling step in `code/data_ingestion.py` or a dedicated script to verify that the streaming ingestion logic respects the 7GB RAM limit. **Constraint**: Must run as part of Phase 2 to ensure scalability before full data processing. **Output**: Verification log confirming RAM usage < 7GB during ingestion. **Dependency**: T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Novel Composition Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest HEA thermodynamic data from the "AFLOW Thermodynamics" dataset (via HuggingFace proxy `foundry-ml/dataset_thermodynamics_aflow`), generate `heas_train.csv`, `holdout_known.csv`, and `true_novel.csv` with strict separation and verification.

**Independent Test**: Verify `heas_train.csv` contains only known entries, `holdout_known.csv` entries exist in the proxy source but not training, and `true_novel.csv` entries return "Not Found" when queried against the proxy source.

**Dataset Strategy**: The "Source API" verification is implemented as a **Static Proxy** against the downloaded `foundry-ml/dataset_thermodynamics_aflow` dataset. This satisfies the Spec's requirement for a "Source API" check while adhering to the Plan's constraint of "No live external API calls" for CI reproducibility. The final report MUST include a disclaimer that "True Novel" candidates are novel relative to this specific snapshot.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T019b [P] [US1] **Verification of Fail-Loudly**: Add a unit test in `tests/unit/test_ingestion.py` that verifies `code/data_ingestion.py` raises an exception when the dataset fetch is simulated to fail, ensuring no synthetic fallback logic exists. **Logic**: Mock the `datasets.load_dataset` call to raise an error; assert the script exits with a non-zero code and no synthetic data is generated. **Assertion**: `pytest.raises(ConnectionError)`. **Dependency**: Requires T002/T003 (Design Spec) to exist. **Ordering**: Test-First: Write this test before implementing T012. **Dependency**: Requires T002/T003.
- [X] T010 [P] [US1] Unit test for data filtering logic in `tests/unit/test_ingestion.py` (verify 5+ element filter).
- [X] T011 [P] [US1] Integration test for dataset split logic in `tests/integration/test_split.py` (verify no overlap between train/holdout/novel).

### Implementation for User Story 1

- [X] T012 [US1] **Ingestion Script Implementation**: Implement `code/data_ingestion.py` to load `foundry-ml/dataset_thermodynamics_aflow` using `datasets.load_dataset(..., streaming=True)`. **Mapping**: `formation_energy_per_atom` -> `target_energy`, `mixing_enthalpy` -> `target_hmix`. Filter for multi-element systems. **Constraint**: Use `streaming=True` to respect RAM limits. **Fail-Loudly Rule**: The script MUST raise a `ConnectionError` or `ValueError` immediately if the dataset fetch fails; NO synthetic data generation or fallback logic is permitted. **Integrity Check**: Implement logic to validate the dataset checksum against `config.EXPECTED_AFLOW_CHECKSUM` (defined in T002) and implement **exponential backoff with a maximum of 3 retries** if the fetch fails (per Spec Edge Case 1). Do NOT use mock logging. **Output**: `code/data_ingestion.py`.
- [X] T017a [US1] **Download Raw Data**: Execute `code/data_ingestion.py` to download the raw `foundry-ml/dataset_thermodynamics_aflow` dataset to `data/raw/`. **Output**: `data/raw/aflow_raw.parquet` (or equivalent). **Constraint**: Must use `streaming=True`. **Checksum**: Must use the static `config.EXPECTED_AFLOW_CHECKSUM` defined in T002 for integrity verification. **Dependency**: T012.
- [X] T017b [US1] **Compute Checksum & Verify**: Compute the SHA256 checksum of `data/raw/aflow_raw.parquet`. Compare it against the *static* `config.EXPECTED_AFLOW_CHECKSUM` defined in T002. If they match, log success; if not, raise an error. **Do NOT** update the config; the checksum is a static constant. **Output**: Verification log. **Dependency**: T017a.
- [X] T016v [US1] **Streaming Integrity Verification**: Run a verification script to assert that the exponential backoff (max 3 retries) and checksum validation logic (implemented in T012) executed correctly against the downloaded artifact. **Logic**: Simulate a fetch failure and assert the retry mechanism triggers a limited number of times before failing, and that the checksum validation rejects an invalid file. **Output**: Verification report. **Dependency**: T012, T017a.
- [X] T019c [US1] **Strict Composition Comparison**: Implement strict composition string comparison check to prevent hash collisions in `code/data_ingestion.py`. **Output**: Produce a `deduplicated composition index` artifact (set of strings) consumed by T014a, T015, and T018a. **Dependency**: T012.
- [X] T014a [US1] **Hold-out Known Sampling**: Sample `config.N_NOVEL_SAMPLES` unique combinations of elements from the *downloaded* `aflow_raw` dataset (excluding those already in the training split) to create the "Hold-out Known" set. **Algorithm**: 1. Load `aflow_raw`. 2. Randomly sample a subset of compositions. 3. Filter out any that are in the training split (defined in T012). 4. Ensure the remaining set contains compositions that exist in the proxy source (by definition of being in `aflow_raw`). **Output**: `data/processed/holdout_known.csv`. **Dependency**: T012, T019c, T017a (Data Availability). **Note**: Does NOT depend on T017c (Proxy Client).
- [X] T014b [US1] **Hold-out Known Export**: Export the verified hold-out set to `data/processed/holdout_known.csv`. **Dependency**: T014a.
- [X] T015 [US1] **True Novel Generation**: **Algorithm**: 1. Generate the candidate pool by computing the Cartesian product of 5 elements from `config.ELEMENT_SOURCE_LIST` (defined in T002). 2. For each candidate composition string, invoke `query_local_proxy` (from T017c) to check existence in the `aflow_raw` dataset. 3. Filter the pool to retain ONLY those candidates where `query_local_proxy` returns "Not Found". 4. Ensure the final set is disjoint from `heas_train.csv` and `holdout_known.csv` via strict string comparison (T019c). **Constraint**: Must use a fixed random seed for reproducibility if sampling is required to limit the pool size (but prioritize exhaustive iteration of the generated pool). **Disclaimer**: The generated "True Novel" set is novel relative to the `aflow_raw` snapshot, not necessarily the global universe. **Output**: `data/processed/true_novel.csv`. **Dependency**: T017c, T019c, T017a (Data Availability).
- [X] T017c [US1] **Local Proxy Client Implementation**: Implement `code/api_client.py` to query the *local* `aflow_raw` dataset (loaded from `data/raw/aflow_raw.parquet`) for composition existence. **Logic**: 1. Accept a composition string. 2. Load the local dataset into memory (or use a fast lookup index). 3. Return `{"status": "Found", "data":...}` or `{"status": "Not Found"}`. **Constraint**: Must handle rate limits (simulated) and timeouts. **Output**: A callable `query_local_proxy(composition_string)` function. **Dependency**: T003 (requirements), T017a (Data Availability).
- [X] T018a [US1] **Static Proxy Verification**: Implement `code/validate_splits.py` to verify disjoint sets and local proxy existence for holdout/novel sets. **Logic**: Assert `len(set(train) & set(holdout)) == 0`, `len(set(train) & set(novel)) == 0`, and `len(set(holdout) & set(novel)) == 0`. Verify `holdout` entries exist in the local proxy (`aflow_raw`) and `novel` entries do not. **Output**: Exit code 0 if valid, 1 otherwise; log counts to stdout. **Dependency**: T017c, T014b, T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

**Goal**: Compute compositional descriptors via `pymatgen` and train Random Forest/Gradient Boosting models with k-fold cross-validation

**Independent Test**: Verify 5-fold CV $R^2$ is calculated, model artifacts (`.pkl`) are generated, and execution completes within 6 hours on CPU without GPU errors.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Unit test for descriptor calculation in `tests/unit/test_descriptors.py` (verify weighted mean/variance for radius, electronegativity, VEC, melting point).
- [X] T020 [P] [US2] Unit test for numerical stability in `tests/unit/test_descriptors.py` (verify clamping of near-zero values to a small positive constant).

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/feature_engineering.py` to calculate weighted mean and variance descriptors (atomic radius, electronegativity, VEC, melting point) using `pymatgen` for all datasets. **Output**: `data/processed/heas_train_features.csv` with columns: `mean_atomic_radius`, `var_atomic_radius`, `mean_electronegativity`, `var_electronegativity`, `mean_VEC`, `var_VEC`, `mean_melting_point`, `var_melting_point`.
- [X] T022 [US2] Implement numerical clamping logic (min threshold $1e-6$) in `code/feature_engineering.py` to prevent division errors.
- [X] T023 [US2] Implement `code/train_models.py` to train `RandomForestRegressor` and `GradientBoostingRegressor` with k-fold cross-validation. **Includes**: Hyperparameter tuning (max_depth, n_estimators) and model saving logic to output `.pkl` artifacts to `data/models/`.
- [X] T024 [US2] Implement hyperparameter tuning (max_depth, n_estimators) within `code/train_models.py`.
- [X] T026 [US2] Add logging for training metrics (mean $R^2$) and execution time in `code/train_models.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Extrapolation Evaluation and Uncertainty Analysis (Priority: P3)

**Goal**: Evaluate models on "Hold-out Known" (error) and "True Novel" (uncertainty) sets, perform statistical tests, and generate final report.

**Independent Test**: Compare $R^2$ on holdout vs training, verify ensemble variance correlates with convex hull distance, and generate ranked candidate report.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T027 [P] [US3] Integration test for evaluation pipeline in `tests/integration/test_evaluation.py` (verify permutation test and Spearman correlation outputs).

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/evaluate.py` to load trained models and predict on `holdout_known.csv`.
- [X] T029 [US3] Implement $R^2$ and MAE calculation for `holdout_known.csv` in `code/evaluate.py` and compare to training $R^2$.
- [X] T030 [US3] Implement prediction on `true_novel.csv` in `code/evaluate.py` with ensemble variance calculation.
- [X] T031 [US3] **Convex Hull Distance**: Implement distance calculation for `true_novel.csv` entries in `code/evaluate.py`. **Algorithm**: Use `scipy.spatial.ConvexHull` on the *training set's* descriptor space (8 columns from T021). For each novel point, compute the Euclidean distance to the nearest facet of the hull. **Fallback**: If `ConvexHull` fails (e.g., singular matrix), automatically switch to Mahalanobis distance calculation using the training set's covariance matrix with regularization parameter set to a sufficiently small magnitude to ensure stability without over-penalizing model complexity.. **Output**: `distance_to_hull` column in the prediction results. **Dependency**: T021.
- [X] T032 [US3] **Statistical Test (Permutation)**: Implement a **Permutation Test** to compare error distributions of training vs. holdout sets in `code/evaluate.py` (satisfying FR-006). **Logic**: 1. **Ground Truth Availability**: The "Hold-out Known" set (T014a) is defined as compositions present in the source API, so ground truth is **guaranteed** to exist in `aflow_raw`. Do NOT check for availability; proceed directly. 2. Calculate the observed difference in mean absolute error (MAE) between training and holdout sets. 3. Pool the errors from both sets. 4. Randomly shuffle the pooled errors and re-split into two groups of the original sizes. 5. Calculate the mean difference for the shuffled groups. 6. Repeat the procedure a sufficient number of times to ensure stable estimation. 7. Calculate p-value as the proportion of shuffled differences >= observed difference. **Output**: p-value. **Constraint**: If the dataset size is insufficient for the permutation test (e.g., < 10 samples in either set), raise a `ValueError` with a clear message; do NOT fall back to a t-test or other method.
- [X] T033 [US3] **Correlation**: Implement Spearman rank correlation test (FR-007) between variance (from T030) and convex hull distance (from T031) in `code/evaluate.py`. **Note**: This metric replaces the Plan's "Perturbation Magnitude" to satisfy Spec FR-005/FR-007, measuring geometric extrapolation distance rather than sensitivity to perturbation. **Output**: Spearman coefficient and p-value.
- [X] T035b [US3] **Statistical Robustness Check**: Ensure `code/evaluate.py` explicitly handles the case where `true_novel` set is empty or too small (< 10 samples) for statistical correlation by raising a `ValueError` with a clear message, rather than returning `NaN` or skipping the test silently.
- [X] T035a [US3] **Threshold Calculation**: Compute a lower percentile of the *training set's* variance distribution to assess the distribution's tail behavior. **Algorithm**: Train an ensemble of multiple independent Random Forest models on the full training set using distinct random seeds. For each sample in the training set, collect the predictions from the ensemble and calculate the variance. Calculate the lower percentile of this distribution. **Note**: Standard Random Forest models do not output variance for single predictions; this ensemble approach is required to generate a variance distribution for the training set, satisfying SC-005. **Output**: A single float value (threshold) to be used by T034.
- [X] T034a [US3] **Candidate Filtering & Ranking**: Implement logic in `code/report.py` to filter candidates where variance <= threshold (from T035a). Sort by `prediction_variance` ASC, then by `distance_to_hull` ASC. Select a representative subset. **Output**: Intermediate list of candidates.
- [X] T034b [US3] **CSV Generation**: Generate `data/processed/top_novel_candidates.csv` with columns: `composition_string`, `predicted_energy`, `variance`, `distance_to_hull`, `rank` from the filtered list in T034a.
- [X] T034c [US3] **JSON Summary Generation**: Generate `data/processed/variance_distribution_summary.json` containing histogram data for the variance distribution relative to the Lower percentile to satisfy SC-005.
- [X] T034d [US3] **Report Assembly**: Implement final report generation in `code/report.py`. **Logic**: Include statistical summary, correlation coefficient from T033, and DFT status from T041. **Requirement**: If `data/processed/dft_validation_status.txt` indicates failure, explicitly include the statement "The uncertainty metric for 'True Novel' candidates is an unvalidated assumption" in the final report summary. **Novelty Disclaimer**: Explicitly state that "True Novel" candidates are novel relative to the `aflow_raw` snapshot and that live API verification was not performed due to CI constraints. **Dependency**: T034a, T034b, T034c, T041.
- [X] T041 [US3] **DFT Attempt**: Implement `code/dft_attempt.py` to attempt DFT calculation on the top novel candidates (from T034a). **Stack**: Use Quantum ESPRESSO (open-source, reproducible) via a pre-configured container image if available. **Logic**: 1. Check if the pre-configured container image for Quantum ESPRESSO is available. 2. If available, generate input files (POTCAR, KPOINTS, etc.) using generic pseudopotentials and submit job with a timeout. 3. Parse output for formation energy. 4. If successful, write `data/processed/dft_results.csv`. 5. If the container is NOT available OR the job fails (time/resource), write `data/processed/dft_validation_status.txt` containing the exact string "DFT attempt failed due to time/resource constraints or missing infrastructure; uncertainty metric is an unvalidated assumption" and exit with code 0. **Constraint**: Must define a concrete workflow; no stubs. **Dependency**: T034a.
- [X] T042 [US3] **Unvalidated Statement**: Ensure `code/report.py` explicitly includes the statement "The uncertainty metric for 'True Novel' candidates is an unvalidated assumption" in the final report summary if `data/processed/dft_validation_status.txt` indicates failure, satisfying FR-009.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Update `README.md` with installation steps and data flow diagram
- [X] T037 Refactor code to remove unused imports and ensure PEP8 compliance
- [X] T039 [P] Additional unit tests in `tests/unit/`
- [X] T040 Run quickstart.md validation

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
- **Critical**: Ensure `code/data_ingestion.py` uses `streaming=True` for `foundry-ml/dataset_thermodynamics_aflow` to respect RAM constraints.
- **Critical**: Ensure `code/data_ingestion.py` samples exactly `config.N_NOVEL_SAMPLES` combinations (T014a, T015) instead of hardcoding a count.
- **Critical**: Ensure `code/feature_engineering.py` clamps near-zero values to a small positive constant to prevent numerical instability.
- **Critical**: Ensure `code/evaluate.py` performs strict composition string comparison to avoid hash collisions.
- **Critical**: Ensure `code/report.py` filters candidates by the 10th percentile variance threshold (T035a) before ranking (T034).
- **Critical**: The "Source API" for novelty verification is now the **Local Proxy** (T017c), implemented against the downloaded `aflow_raw` dataset.
- **Critical**: The sampling strategy for "True Novel" (T015) must explicitly iterate through the generated combinations and verify their absence in the local proxy via a fast lookup structure (e.g., a pre-computed set of composition strings from T017c) to avoid false positives.
- **Critical**: The convex hull distance calculation (T031) must use `scipy.spatial.ConvexHull` on the training set's descriptor space (specifically the 8 columns generated by T021) and compute the distance of novel points to the nearest facet or vertex, handling points inside the hull correctly (distance = 0). **Fallback**: If ConvexHull fails, use Mahalanobis distance with regularization parameter 1e-6.
- **Critical**: The permutation test (T032) and Spearman correlation (T033) must handle edge cases where the dataset size is small or variances are zero, potentially using `scipy.stats.permutation_test` and `scipy.stats.spearmanr` with `nan_policy='omit'`.
- **Critical**: The final report (T034) must include a disclaimer about the limitations of the "True Novel" set being generated synthetically via sampling rather than discovered via a global search, and explicitly state the sample size and seed used.
- **Critical**: Ta must calculate the th percentile deterministically (10 models, seeds 0-9) and pass it to T034 without intermediate files to ensure reproducibility.
- **Critical**: **Data Integrity**: T012 and T019b must ensure the loader fails loudly on fetch errors. No synthetic fallbacks are permitted.
- **Critical**: **Statistical Robustness**: T035b must ensure statistical tests fail loudly if input data is insufficient, rather than returning silent `NaN` values.
- **Critical**: **Hold-out Logic**: T014a must derive "Hold-out Known" by sampling from the downloaded AFLOW union and excluding the training set, strictly following the Spec's definition.
- **Critical**: **Metric Alignment**: T031 and T033 must use Convex Hull Distance as per Spec FR-005, overriding the Plan's "Perturbation Magnitude" to satisfy the Spec's explicit requirement.
- **Critical**: **DFT Validation**: T041 and T042 must ensure that if DFT fails, the report explicitly states the uncertainty metric is an unvalidated assumption. T041 must use a concrete DFT stack (Quantum ESPRESSO) or a pre-configured container, and generate actual input files if available.
- **Critical**: **API Simulation**: T017c (Local Proxy) must be implemented and invoked by T014a, T015 to satisfy the Spec's requirement for "Source API" verification using the static proxy.
- **Critical**: **Task Ordering**: All tasks are now ordered to respect data dependencies (Producers before Consumers). T012 precedes T017a (Execution). T017a precedes T017b. T017b precedes T016v. T019c precedes T014a, T015. T014a does NOT depend on T017c.