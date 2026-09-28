# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Input**: Design documents from `/specs/001-impurity-clustering-segregation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[B]**: Blocking prerequisite (must complete before downstream tasks)
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

**Purpose**: Project initialization, basic structure, and core validation utilities required by downstream tasks.

- [ ] T001 [P] **REVISED**: Initialize project directory structure: Create root directory `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/` and subdirectories `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/integration/` idempotently.
- [ ] T001b [P] **REVISED**: Initialize project metadata: Create `.gitignore` (excluding `data/`, `results/`, `*.pyc`, `__pycache__`) and `README.md` (with project title and placeholder execution instructions) in `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.
- [ ] T003 [P] **REVISED**: Configure linting (ruff) and formatting (black) tools in `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.
- [ ] T004a [P] **REVISED**: Implement `contracts/dataset.schema.yaml` defining required fields and types. **Action**: Create the file with the following content:
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 required:
 - bulk_config_id
 - impurity_species
 - alloy_system_id
 - clustering_descriptors
 properties:
 bulk_config_id:
 type: string
 impurity_species:
 type: string
 alloy_system_id:
 type: string
 clustering_descriptors:
 type: object
 required:
 - rdf_peak
 - pair_corr
 - voronoi_count
 properties:
 rdf_peak:
 type: number
 pair_corr:
 type: number
 voronoi_count:
 type: number
 segregation_energy:
 type: number
 nullable: true
 ```
 Save to `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/contracts/dataset.schema.yaml`.
- [ ] T004b [P] **REVISED**: Implement `contracts/output.schema.yaml` defining required fields and types. **Action**: Create the file with the following content:
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 required:
 - r2
 - rmse
 - p_values
 - vif_scores
 properties:
 r2:
 type: number
 rmse:
 type: number
 p_values:
 type: object
 additionalProperties:
 type: number
 confidence_intervals:
 type: array
 items:
 type: object
 required:
 - lower
 - upper
 - predicted
 properties:
 lower:
 type: number
 upper:
 type: number
 predicted:
 type: number
 vif_scores:
 type: object
 additionalProperties:
 type: number
 sensitivity_metrics:
 type: object
 additionalProperties:
 type: number
 ```
 Save to `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/contracts/output.schema.yaml`.
- [ ] T004c [B] **REVISED**: Implement `code/validators.py` with function `def validate_citations(url: str, metadata_path: str) -> dict`.
 1. Parse `metadata_path` (data/metadata.yaml) to extract URLs.
 2. Check extracted URLs against a hardcoded whitelist: `['https://materialsproject.org', '']`.
 3. Verify the URL exists via HTTP HEAD request. For OQMD, verify it returns a valid JSON response using the specific endpoint `/materials/composition/{composition_id}`.
 4. Return a status dict: `{"success": True, "error_code": None, "message": "OK"}` if valid.
 5. Return `{"success": False, "error_code": "URL_INVALID", "message": "URL not in whitelist or unreachable"}` if invalid.
 6. **Note**: This task returns a status object instead of raising an exception to support graceful error handling in the pipeline.
 7. **Dependency**: Must be completed before T013. **Constraint**: Do NOT mark as [P] (parallel-safe) as it is a blocking prerequisite for Phase 3.
- [ ] T005 [P] Create `code/config.py` for paths, random seeds, hyperparameters, and the `VALIDATED_SOURCE_WHITELIST` list (MP/OQMD URLs).
- [ ] T005b [P] Generate the methodology sketch in `docs/methodology.md` defining the k-fold CV procedure, random seed (fixed), and LOOCV fallback logic.
- [ ] T006 [P] Setup `code/data/__init__.py` and `code/modeling/__init__.py`.
- [ ] T008 [P] Setup `data/raw/`, `data/processed/`, and `results/` directory structure with `.gitkeep`.
- [ ] T009 [P] Create `tests/unit/` and `tests/integration/` scaffolding.
- [ ] T017a-0 [B] **REVISED**: **Scope Definition**: Define the dynamic resolution logic for the 'deferred' sample size and alloy systems required by FR-003.
 1. **Logic**: Create a configuration file `data/scope_config.yaml` defining:
 - `min_alloy_systems`: 3 (target)
 - `alloy_systems`: ['Fe-Cr', 'Ni-Mo', 'Cu-Zn'] (candidate list)
 - `power_analysis_params`: {alpha:, power: sufficient statistical power to detect the hypothesized effect, effect_size: a medium magnitude}
 - `max_samples`: 500 (hard cap)
 2. **Output**: Save to `data/scope_config.yaml`.
 3. **Dependency**: Must be completed before T017a-1. **Blocking**: Blocks Phase 3 simulation tasks.
 4. **Note**: The actual sample size will be determined dynamically by the pipeline (see T017c) based on power analysis, not hardcoded here.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes the pipeline skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [US1] Implement `code/main.py` pipeline orchestration with error handling and logging. Logic:
 1. Define the *logical* sequence: `download_bulk_configs` -> `build_gb_supercells` -> `compute_descriptors` -> `run_simulation`.
 2. **Note**: This task defines the orchestration flow. The actual implementation of `download.py` (T013), `gb_builder.py` (T014), etc., occurs in Phase 3. The code in T007 will call these modules once they are implemented.
 3. Ensure the script handles the `[DATA_UNAVAILABLE]` error from T013 gracefully by logging and exiting cleanly.
 4. This task is a skeleton and cannot be fully executed until Phase 3 modules exist.
 5. **Constraint**: Do NOT mark as [P] (parallel-safe) as it implies independent execution, which is not true for a skeleton calling unimplemented modules.
- [ ] T010 [P] [US1] Unit test for retry logic in `tests/unit/test_download_retry.py`.
- [ ] T011 [P] [US1] Unit test for interface-region descriptor filtering in `tests/unit/test_descriptor_interface.py`.
- [ ] T012a [P] [US1] **REVISED**: Integration test for full data pipeline in `tests/integration/test_data_pipeline.py`. Logic: Execute the pipeline on a small sample of bulk configurations (N=10) and verify that GB supercells are constructed, descriptors are computed, and energies are generated with non-empty values saved to disk.
- [ ] T012b [P] [US1] **REVISED**: Artifact verification test. Logic: Verify that `data/processed/gb_supercells/`, `data/processed/descriptors.csv`, and `data/processed/segregation_energies.csv` exist and contain non-empty data.
- [ ] T012c [P] [US1] Unit test for segregation energy generation verification in `tests/unit/test_energy_generation.py`. Logic: Verify that `simulate_energy.py` produces non-empty results and logs the count of generated energies. Tag [FR-003].

**Checkpoint**: Foundation and testing scaffolding ready.

---

## Phase 3: User Story 1 - Data Pipeline and Clustering Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download bulk configurations (MP/OQMD), construct GB supercells, compute clustering descriptors (RDF, pair correlation, Voronoi-based neighbor counts) in the interface region, and generate segregation energies via simulation (since energies are NOT in MP/OQMD).

**Independent Test**: Can be fully tested by executing the data pipeline script on a representative sample of bulk configurations, verifying that GB supercells are constructed, impurities are inserted at the interface, descriptors are computed from the interface region, and segregation energies are generated via simulation, with non-empty values saved to disk.

**⚠️ PLAN AMENDMENT**: The `plan.md` instruction to "Apply PCA to descriptors" in Phase 1 is REJECTED. Spec FR-007 mandates retaining raw descriptors to detect and report collinearity (VIF ≥ 10) without feature removal or transformation. All tasks in this phase follow the Spec, not the Plan's contradictory instruction.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data/download.py` with function `def download_bulk_configs(url: str, max_retries: int = 3) -> Path`.
 1. MUST invoke `validate_citations(url, 'data/metadata.yaml')` from `code/validators.py` (T004c) **after T004c is completed**.
 2. MUST log `[DATA_UNAVAILABLE] URL=<url> attempts=3` after 3 failed attempts.
 3. **CRITICAL**: If `max_retries` is reached and validation fails, write an entry to `data/inaccessible_manifest.json` with the URL and timestamp to permanently mark the dataset as inaccessible, then attempt to load from `data/raw/backup/` if available. If backup is empty, raise `[DATA_UNAVAILABLE]` and exit cleanly.
 4. This task fetches bulk structures from MP/OQMD. **Dependency**: Requires T004c completion.
- [ ] T013b [US1] **REVISED**: Implement OQMD-specific download logic in `code/data/download.py`.
 1. **Logic**: If the URL contains 'oqmd.org', use `requests` to fetch from `/materials/composition/{composition_id}` with specific API parameters.
 2. **Validation**: Verify the response is valid JSON and contains the required bulk configuration fields.
 3. **Output**: Save to `data/raw/oqmd_configs/`.
 4. **Dependency**: Requires T004c completion.
- [ ] T014 [P] [US1] **REVISED**: Implement `code/data/gb_builder.py` to construct GB supercells and insert impurities at the interface.
 1. **Logic**: Use `pymatgen.symmetry.bandstructure.HighSymmKpath` to determine misorientation angles for Fe-Cr BCC (100) tilt GB. Use `pymatgen.GBBuilder` with specific misorientation angles (e.g., representative values). and boundary planes.
 2. **Input**: Bulk configuration files from `data/raw/`.
 3. **Output**: GB supercell structures saved to `data/processed/gb_supercells/`.
 4. **Constraint**: Ensure the builder is deterministic using seeds from `config.py`.
 5. **Dependency**: Requires T013 completion.
- [ ] T019 [B] [US1] **REVISED**: Implement filtering logic for bulk configurations with zero impurity atoms; log exclusion count to `data/processed/preprocessing_report.json`.
 1. **Logic**: Filter configurations where `impurity_count == 0`.
 2. **Output**: Generate `data/processed/preprocessing_report.json` with the exact schema:
 ```json
 {
 "total_configs": <int>,
 "excluded_configs": <int>,
 "exclusion_reason": "zero_impurity_atoms"
 }
 ```
 3. **Dependency**: Must run after T013. **Blocking**: Blocks T015 and T017c.
- [ ] T015 [US1] Implement `code/data/descriptors.py` to compute RDF peaks, pair correlation statistics, and Voronoi-based neighbor counts specifically within the GB interface region (FR-002).
 1. **Logic**: Compute only for atoms within 5 Å of the GB plane.
 2. **Constraint**: **DO NOT apply PCA or dimensionality reduction**. Output raw values for all three descriptor types to `data/processed/descriptors.csv` with columns [species, rdf_peak, pair_corr, voronoi_count].
 3. **Atomicity**: Implement all three descriptor types in a single cohesive function to ensure atomic execution and consistent file output.
 4. Output: `data/processed/descriptors.csv`.
 5. **Dependency**: Must be completed after T014 (GB Builder) and T019 (Preprocessing Report).
- [ ] T016 [P] [US1] Implement logic in `code/data/descriptors.py` or a new helper to extract and tag each configuration with its `alloy_system_id` based on impurity species and bulk crystal structure.
 1. **Logic**: Generate `alloy_system_id` as `f"{crystal_system}_{impurity_species}"` (e.g., 'BCC_Cr'). `crystal_system` must be derived deterministically from the bulk configuration file using pymatgen's `get_space_group_symbol` or `lattice` properties (e.g., 'BCC', 'FCC').
 2. Output: `data/processed/alloy_systems.json`.
 3. **Dependency**: Must be completed after T015. **Can run in parallel with T018 ONLY after T014 is complete**.
- [ ] T017a-1 [B] [US1] **REVISED**: **System-Specific Potential Download**: Implement a script `code/data/download_potentials.py` to download potentials for ALL systems defined in `data/scope_config.yaml` (T017a-0).
 1. **Logic**: Iterate over `data/scope_config.yaml` and call `PotentialLoader` for each system.
 2. **Specifics**: Use the specific NIST URL for Fe-Cr. For Fe-Cr, use potential ID 'Fe_Cr.eam.fs'.
 3. **Constraint**: If a potential is not found in NIST for a detected system, raise a `FileNotFoundError` and log a warning. **Do NOT skip the system**; the pipeline must fail loudly to ensure FR-003 compliance.
 4. **Output**: Save verified files to `data/potentials/`.
 5. **Metadata**: **CRITICAL**: Upon successful download, compute the SHA256 checksum of the file and record the `potential_id`, `url`, `checksum`, and `timestamp` in `data/metadata.yaml` to satisfy Constitution Principle VI.
 6. **Dependency**: Requires T017a-0 completion. **Must be completed before T017c**. **Do NOT mark as [P]**.
- [ ] T017a [US1] Define the 'structurally perturbed representation' logic and 'specific NIST EAM potential' parameters in `code/data/simulate_energy.py` constants:
 1. **Perturbation**: Apply a random atomic displacement to all atoms in the GB supercell. **MUST use `rng = numpy.random.default_rng(seed=config.RANDOM_SEED)`** (from T005) and displacement `rng.normal(loc=0.0, scale=0.01, size=structure.num_atoms) * vector`. This ensures deterministic reproducibility (Constitution Principle I).
 2. **Vector Definition**: `vector` MUST be the unit vector along the GB plane normal, calculated via `structure.get_interface_normal()` (or equivalent pymatgen method on the GB supercell object). If the normal vector is zero, raise an error.
 3. **Potential**: Use the specific NIST EAM potential for the alloy system defined in `data/scope_config.yaml` (file path: `data/potentials/{system_id}.eam.fs`). **Note**: While the MVP uses Fe-Cr, the code must be structured to accept a generic `potential_path` argument to support FR-003's requirement for multiple systems.
 4. **Rationale**: This minimal perturbation breaks the exact symmetry of the input structure to avoid circularity while remaining physically plausible for a "distinct representation".
 5. **Dependency**: Requires T014 (GB Builder) and T005 completion.
- [ ] T017b [US1] Implement the simulation engine in `code/data/simulate_energy.py` that applies the perturbation logic from T017a and calculates segregation energy using the NIST EAM potential. **Action**: The engine must accept a `potential_path` parameter (defaulting to the Fe-Cr path from T017a-1) to allow generic usage for FR-003. This task implements the engine (physics logic) using the parameters defined in T017a. **Dependency**: Requires T014 (GB Builder) and T017a completion.
- [ ] T017c [US1] Implement `code/data/simulate_energy.py` runner function `run_simulation` to execute the engine on the generated GB supercells and output `data/processed/segregation_energies.csv`.
 1. **Logic**: Iterate over valid GB supercells (post-filter T019).
 2. **Dynamic Sample Size**: Implement a loop that generates samples, runs power analysis, and continues until `N >= required_power` OR `N >= max_samples` (from T017a-0). Log the final N and stopping condition.
 3. **Output**: `data/processed/segregation_energies.csv`.
 4. **Dependency**: Requires T017a, T017b, T017a-1, and T019 completion.
- [ ] T017d [US1] Verify that `data/processed/segregation_energies.csv` contains non-empty energy values and logs the count of generated energies.
- [ ] T017e [US1] Verify that `data/processed/segregation_energies.csv` contains the `alloy_system_id` and `cluster_metadata` columns linked to the energy values, satisfying the Independent Test for US-1.
- [ ] T018 [B] [US1] **REVISED**: Implement `code/data/descriptor_filter.py` to compute VIF (Variance Inflation Factor) on descriptors. **Action**: Calculate VIF for each descriptor. **IF VIF >= 10 THEN** generate a descriptive report `data/processed/collinearity_report.md` explaining joint relationships. **ELSE** generate a report stating "No collinearity detected (VIF < 10)". **Do NOT remove features** in this task; only report. (FR-007). Report format: VIF scores per feature, descriptive text for joint relationships (or confirmation of independence), no feature removal.
 1. **Descriptive Framing**: If VIF >= 10, the report MUST state: "Feature X and Y are collinear (VIF=X). Interpret as a joint effect of [cluster size/density] rather than independent predictors."
 2. **Dependency**: Must run after T015. **Logical placement**: Execute immediately after T015. **Parallel**: Can run in parallel with T017c. **Blocking**: Blocks T023.
- [ ] T019c [US1] Implement streaming logic in `code/data/download.py` for large bulk configuration archives. **Action**: If a dataset exceeds 1GB, use `requests` with `stream=True` and iterate line-by-line or chunk-by-chunk to process the data without loading it entirely into RAM. Log the streaming status and chunk count.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a lightweight regression model (Linear Regression for MVP p-values), perform 5-fold CV (or LOOCV), and report R², RMSE, and p-values (coefficients for Linear).

**Independent Test**: Can be fully tested by running the training script on a held-out test set of samples and verifying that R², RMSE, and p-values are computed and saved with valid numeric outputs.

**⚠️ Dependency**: This phase requires completion of Phase 3 (US1), specifically T017c (energies), T015 (descriptors), T018 (collinearity report), and T016 (alloy grouping).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for CV split logic in `tests/unit/test_cv_split.py`.
- [ ] T021 [P] [US2] Unit test for metric calculation (R², RMSE, p-values) in `tests/unit/test_metrics.py`.
- [ ] T022 [P] [US2] Integration test for model training and evaluation in `tests/integration/test_model_training.py`.

### Implementation for User Story 2

- [ ] T027 [US2] **REVISED**: Add contract validation in `code/modeling/train.py` to validate input against `contracts/dataset.schema.yaml` BEFORE training.
- [ ] T023 [US2] Implement `code/modeling/train.py` with **Linear Regression** as the primary model for the MVP to satisfy the 'coefficient p-values' requirement (US-2).
 1. **Cross-Validation**: Implement a **manual k-fold CV loop** using `sklearn.model_selection.GroupKFold` (or LOOCV). **Logic**: **IF N >= 5 THEN** use 5-fold CV. **ELSE** use LOOCV. For each fold:
 - Instantiate `statsmodels.api.OLS` on the training fold.
 - Fit the model.
 - **Extract `result.pvalues` for each feature** and save them to `results/metrics_per_fold.json` (one entry per fold).
 - Compute R², RMSE on the test fold.
 - Aggregate metrics across folds.
 2. **Collinearity**: If `data/processed/collinearity_report.md` (from T018) indicates VIF >= 10, log a warning that p-values may be unstable, but proceed with raw data (as per FR-007 "frame, don't remove").
 3. **Confidence Intervals**: Calculate confidence intervals for predictions as required by US-2.
 4. Save metrics to `results/metrics.json` with SHA256 hash recorded in `state/project.yaml` under key `code_version_hash` for provenance.
 5. **Dependency**: Requires T015, T017c, and T018 completion.
- [ ] T025 [US2] Implement per-system evaluation logic to report R² values for each alloy system separately. **Dependency**: Requires `alloy_systems.json` from T016 to group samples. Use the `alloy_system_id` format defined in T016 (`f"{crystal_system}_{impurity_species}"`). If `alloy_systems.json` is missing, raise an error.
- [ ] T025c [US2] **REVISED**: **Sample Size Enforcement**: Implement logic to dynamically calculate and enforce the minimum sample size for held-out systems.
 1. **Logic**: Perform power analysis to determine the minimum number of samples required per system to achieve statistical significance.
 2. **Parameters**: Use alpha=0.05, power=0.8, effect_size=0.5.
 3. **Constraint**: If the dataset size is below the threshold, raise a `ValueError` and log the required sample size.
 4. **Output**: Save the calculated threshold to `results/sample_size_threshold.json`.
 5. **Dependency**: Must be completed before T025b.
- [ ] T025b [US2] Implement the 'held-out alloy system' split and evaluation logic required by SC-001, **including permutation testing for statistical significance**.
 1. **Split**: Split the dataset such that entire `alloy_system_id` groups are held out as the test set using `GroupKFold`. The number of held-out systems is determined by the actual number of groups in the data (adaptive).
 2. **Permutation Testing**: Implement a permutation test procedure:
 - Shuffle the target variable (segregation energy) N times (N=1000 if N_groups >= 5, else N=100 * N_groups).
 - For each shuffle, re-train the model and compute R².
 - Compare the observed R² against the null distribution.
 - Calculate p-value as the fraction of shuffled R² values >= observed R².
 3. **Output**: Save to `results/sc001_held_out_metrics.json` with keys: `r2`, `rmse`, `p_value_permutation`, `null_distribution_stats`, `n_groups_tested`.
 4. **Dependency**: Requires T025 and T025c completion. **Note**: T025b is self-contained and does not depend on T044 (which has been removed).
- [ ] T026 [US2] Implement per-prediction confidence interval calculation. Logic: Use `statsmodels` OLS `get_prediction()` method to generate confidence intervals for each prediction in the test set. Output: `results/confidence_intervals.json` with keys [sample_id, predicted_energy, ci_lower, ci_upper]. **Dependency**: Requires T023 completion.
- [ ] T028 [US2] **REMOVED**: Logic merged into T023 to avoid race conditions and redundant writes.
- [ ] T043 [US2] **REMOVED**: Logic merged into T025b. Permutation testing (if needed) is now a sub-step of T025b with adaptive N.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds (regularization, descriptor perturbation) and hypothesis testing with multiple-comparison correction.

**Independent Test**: Can be fully tested by executing the sensitivity analysis script on a sample of predictions and verifying that at least 3 threshold values are swept and corresponding RMSE variance changes are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`.
- [ ] T030 [P] [US3] Unit test for multiple-comparison correction (Bonferroni/FDR) in `tests/unit/test_hypothesis.py`.
- [ ] T031 [P] [US3] Integration test for full hypothesis and sensitivity analysis in `tests/integration/test_hypothesis_sensitivity.py`.

### Implementation for User Story 3

- [ ] T036 [US3] Add contract validation in `code/modeling/evaluate.py` to validate output against `contracts/output.schema.yaml` BEFORE analysis.
- [ ] T032 [US3] Implement `code/modeling/evaluate.py` with sensitivity analysis. Logic: Sensitivity analysis sweeps over at least 3 concrete values of:
 1. **Data-Driven Thresholds**: First, analyze the distribution of the training data (e.g., quantiles of descriptor values or learned regularization paths).
 2. **Regularization strength**: Use Ridge regression with alpha values derived from the data distribution (e.g., `[0.0, 0.1 * max_alpha, 1.0 * max_alpha]` where `max_alpha` is the value where coefficients become negligible).
 3. **Descriptor perturbation magnitude**: Use values derived from thermal vibration heuristics or data quantiles (e.g., `[0.0, 0.01, 0.05]` Å if supported by data, otherwise derived from std dev of descriptors).
 4. **Aggregation**: Calculate `rmse_variance` (variance of RMSE across folds) and `r2_stability` (standard deviation of R² across folds) for each threshold.
 5. **Output**: Report RMSE variance and R² stability across the sweep. Output file: `results/sensitivity_report.json` with structure: `{"thresholds": [{"alpha": 0.0, "rmse_variance": 0.01, "r2_stability": 0.95, "data_relevant": true},...]}` [FR-006].
- [ ] T033 [US3] **REMOVED**: Logic merged into T032 to ensure single aggregation point for stability metrics.
- [ ] T034a [US3] Implement logic to extract predictor significance: If Linear Regression (T023), extract coefficients and standard errors; if RandomForest (not used), compute permutation importance. Output to `results/feature_importance.json`.
- [ ] T034 [US3] Implement hypothesis testing for predictor coefficients (from T034a) with Bonferroni or FDR correction (FR-005) [FR-005].
- [ ] T035 [US3] Implement logic to handle non-significant results (p > 0.05) by documenting null results with p-values in `results/null_results_report.json`.
- [ ] T037 [US3] Save sensitivity report to `results/sensitivity_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update `README.md` with execution instructions and data provenance details.
- [ ] T039 Code cleanup and refactoring for consistency.
- [ ] T040 [P] Add additional unit tests for edge cases (collinearity, missing data) in `tests/unit/`.
- [ ] T041 Run quickstart.md validation to ensure all scripts execute correctly on CPU-only runner.
- [ ] T042 [P] **REVISED**: Verify all tasks run within 6 hours on CPU cores with sampled dataset.
 1. **Criteria**: Execute the full pipeline on a **sampled dataset of ≤500 configurations** (as per Plan.md Performance Goals).
 2. **Verification**: Log the exact dataset size (N) and wall-clock time.
 3. **Pass Condition**: Time ≤ 6 hours AND N ≤ 500.
 4. **Output**: `results/performance_verification.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**:
 - **Phase 3 (US1)**: Depends on Foundational (Phase 2). **Specifically requires T004c, T017a-0, and T017a-1 completion**.
 - **Phase 4 (US2)**: Depends on **completion of Phase 3 (US1)**, specifically T015, T016, T017c, and T018.
 - **Phase 5 (US3)**: Depends on completion of Phase 4 (US2).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST wait for US1 data output** (T017c, T016, T018)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **Phase 3 (US1) must complete before Phase 4 (US2) begins**.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if US1 data is pre-generated or mocked for US2/US3 development, but final execution must be sequential.**

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for retry logic in tests/unit/test_download_retry.py"
Task: "Unit test for interface-region descriptor filtering in tests/unit/test_descriptor_interface.py"
Task: "Integration test for full data pipeline in tests/integration/test_data_pipeline.py"
Task: "Unit test for segregation energy generation verification in tests/unit/test_energy_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py with retry logic"
Task: "Implement code/data/gb_builder.py to construct GB supercells"
Task: "Implement code/data/descriptors.py for interface region descriptors"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model) - **Can develop logic but must wait for US1 data for final run**
 - Developer C: User Story 3 (Analysis) - **Can develop logic but must wait for US2 output for final run**
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [B] tasks = blocking prerequisites (strictly sequential)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on a CPU-only GitHub Actions runner with limited CPU and memory resources.; no GPU, no 8-bit/4-bit models, no deep learning.
- **Data**: All data must be real (MP/OQMD structures + Simulation energies); no fabrication or synthetic placeholders. **Fallback**: If OQMD/MP fail, the pipeline MUST attempt to load from a local `data/raw/backup/` directory if present, otherwise fail with `[DATA_UNAVAILABLE]` and exit. No synthetic data generation is permitted.
- **Scientific Constraint**: Segregation energies are generated via simulation (T017) because they are not available in MP/OQMD. Bulk structures are sourced from MP/OQMD (T013).
- **Reproducibility**: All random operations (perturbations, splits) MUST use seeds from `code/config.py`.
- **Plan Correction**: The Plan's mention of PCA in 'Phase 1' is an error; Spec FR-007 (report, don't remove) and Task T015 take precedence. **This Plan Amendment is recorded in the Phase 3 header and T015.**
- **Constitution Note**: The `[DATA_UNAVAILABLE]` state does not fail the "Verified Accuracy" gate if the pipeline handles it gracefully (retry logic) and logs the error; the gate only fails if the data source is invalid or unreachable without retry.
- **New Revision Concern**: T019b and T019c added to enforce "Fail Loudly" and "Stream Real Data" principles, preventing synthetic fallbacks and ensuring large datasets are handled via streaming rather than shrinking to toy sets.