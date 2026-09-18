# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Input**: Design documents from `/specs/001-predict-plant-metabolite-profiles/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e., US1, US2, US3)
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

- [ ] T001a [P] Create core directory structure: `code/`, `code/data/`, `code/modeling/`, `code/utils/`, `code/cli/`, `data/raw/`, `data/processed/`, `data/interim/`
- [ ] T001b [P] Create test directory structure: `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 Initialize Python project with pinned dependencies (`scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `pymc3`, `tqdm`, `pydantic`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T004 must be completed first** to enable schema enforcement for all downstream data tasks.

- [X] T004 Create Pydantic models for `Species`, `BGCFeature`, `Metabolite`, and `ModelOutput` in `code/models/schemas.py` to enforce runtime schema validation per Constitution Principle III.
- [X] T005 [P] Implement configuration loader in `code/config.py` to manage species lists, thresholds, and data paths
- [X] T005b [P] Implement `seed_manager` in `code/config.py` to set and retrieve global random seeds for reproducibility (Constitution Principle I); update T023a, T023b, T024, T026 to use `config.seed_manager.get_seed()`.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and console handlers
- [X] T007 Setup data directory structure creation, checksum verification logic for **derived artifacts** (`data/processed/aligned_matrix.csv`, `data/interim/pca_features.csv`, `data/processed/metrics.json`), AND logic to update the `updated_at` timestamp in `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` on every artifact write. **Logic**: For each derived artifact written, compute its SHA-256 checksum and record it in `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` under `artifact_hashes`. This satisfies Constitution Principle III (Data Hygiene) and V (Versioning).
- [ ] T008 Setup environment variable management for API keys (if needed) and local paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Alignment and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Automatically download genomic assemblies and metabolite tables, run antiSMASH, and generate an aligned matrix.

**Independent Test**: Execute the pipeline on a small subset (5 species) and verify the output CSV contains non-null values for both BGC counts and metabolite abundances, completing within 30 minutes on CPU.

### Implementation for User Story 1

- [X] T012 [US1] Implement `download_genomes()` in `code/data/download.py` to fetch FASTA/GFF. **Logic**: Iterate through the species list. For each species, attempt NCBI RefSeq. If RefSeq fails (network error, empty result, or >500MB genome), **skip that specific species**, log a warning with the species name, and continue to the next. **Do NOT attempt secondary sources (Phytozome)**. **Do NOT use synthetic data**. The pipeline must succeed with partial data if some species are unavailable, but must fail loudly if *all* species fail.
- [X] T013 [US1] Implement `download_metabolites()` in `code/data/download.py` to fetch abundance tables. **Logic**: Iterate through the species list. For each species, attempt PMDB. If PMDB fails, **skip that specific species**, log a warning with the species name, and continue. **Do NOT attempt secondary sources (MetaboLights)**. **Do NOT use synthetic data**.
- [X] T014 [US1] Implement `run_antiSMASH_wrapper()` in `code/data/preprocess.py` to execute the antiSMASH pipeline and parse JSON output to generate a binary presence matrix and a count matrix for BGC diversity
- [X] T016 [US1] Implement `harmonize_metabolites()` in `code/data/preprocess.py` to apply InChIKey normalization, pseudo-count +1, and log-transformation
- [X] T015 [US1] Implement `map_bgc_to_metabolite()` in `code/data/preprocess.py` using the MIBiG ontology to map BGC types to metabolite classes. Explicitly implement a fallback to Pfam HMMs for plant-specific clusters to reduce the 'unknown' rate; if no match is found in MIBiG or Pfam, assign to 'unknown' class.
- [X] T017 [US1] Implement `align_data()` in `code/data/align.py` to merge genomic and metabolomic data by species. **Logic**: Filter out rows where data is missing (NaN/None) in either modality. **CRITICAL**: Explicitly **preserve** rows where BGC count is zero (valid biological state) and do not treat them as missing data. Calculate the alignment success rate (SC-004) against the original input list and log the count of excluded species.
- [X] T017b [US1] Implement `calculate_alignment_success_rate()` in `code/data/align.py` to compute the percentage of input species with valid data in both modalities. Write this metric to `data/processed/alignment_stats.json`, include it in the final report, AND record it in the project state file `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` as required by SC-004.
- [X] T018 [US1] Implement `save_aligned_matrix()` in `code/data/align.py` to write the final CSV to `data/processed/aligned_matrix.csv`. **Logic**: Ensure zero BGC count rows are explicitly preserved in the output file as valid data points per the Edge Cases requirement.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for genome size filter logic in `tests/unit/test_download.py`
- [X] T010 [P] [US1] Unit test for InChIKey harmonization in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Integration test for end-to-end data alignment on 3 mock species in `tests/integration/test_align.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train regression models (RF, Elastic Net, PGLS) with phylogenetic stratification and validate against a permutation baseline.

**Independent Test**: Run training on the P1 dataset, verify R² > 0 for PGLS, and confirm phylogenetic permutation baseline yields R² near zero.

- [X] T021 [US2] Implement `load_phylogeny()` in `code/modeling/phylo.py` to load species tree data (Newick format) from `data/raw/phylogeny/` for stratification
- [X] T021b [US2] Implement `construct_covariance_matrix()` in `code/modeling/phylo.py` using `dendropy` to generate the phylogenetic covariance matrix from the tree loaded in T021
- [X] T023a-PCA [US2] Implement `apply_pca()` in `code/modeling/train.py` to apply PCA for dimensionality reduction before multivariate modeling to prevent overfitting (N < 50 vs high features). Output saved to `data/interim/pca_features.csv`.
- [X] T023a [US2] Implement `train_models_orchestrator()` in `code/modeling/train.py` to determine sample size N. **Logic**: If N < 20, route execution to T023a-LOO; if N >= 20, route execution to T023b. **Justification**: This deviation from FR-005's 5-fold CV is explicitly documented in `plan.md` under "Complexity Tracking" to ensure statistical stability with small N. This task acts as the flow controller.
- [X] T023a-LOO [US2] Implement `train_models_loo()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting using Leave-One-Out CV. **Only run if routed by T023a**. Use PCA-reduced features from T023a-PCA. **Justification**: See `plan.md` "Complexity Tracking" for deviation from FR-005 (5-fold) due to N < 20. This task is mutually exclusive with T023b.
- [X] T023b [US2] Implement `train_models_5fold()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting with 5-fold CV. **Only run if routed by T023a (N>=20)**. Use PCA-reduced features from T023a-PCA. **Justification**: See `plan.md` "Complexity Tracking" for standard 5-fold CV usage when N >= 20. This task is mutually exclusive with T023a-LOO.
- [X] T024 [US2] [PRIMARY] Implement `train_pgls()` in `code/modeling/phylo.py` using `statsmodels` and the phylogenetic covariance matrix from T021b (constructed via `dendropy`) to account for non-independence. **Dependency**: **MUST consume PCA-reduced features from T023a-PCA** to satisfy dimensionality reduction constraints and prevent overfitting. This task produces the PRIMARY analysis output per FR-010.
- [X] T024b [US2] Implement `report_primary_results()` in `code/modeling/eval.py` to explicitly extract, format, and log the PGLS R² and feature importance as the primary result for the final report, ensuring FR-010 compliance.
- [X] T022 [US2] Implement `create_stratified_split()` in `code/modeling/train.py` to split data by phylogenetic clade
- [X] T025 [US2] Implement `evaluate_models()` in `code/modeling/eval.py` to calculate R² and Pearson correlation on hold-out sets
- [X] T026 [US2] Implement `run_phylogenetic_permutation()` in `code/modeling/eval.py` to shuffle labels (metabolite abundances) while keeping features and tree structure intact to generate the null distribution. **Execution Order**: **Must run AFTER** model training (T024/T023) and evaluation (T025) to allow comparison of the model's R² against the baseline. This ensures the baseline is a valid null model for the trained predictors.
- [X] T027 [US2] Implement `calculate_significance()` in `code/modeling/eval.py` to compare model R² against baseline (from T026), calculate the p-value, and log the significance result (p < 0.05 check) to `data/processed/metrics.json` as required by FR-006.
- [X] T028 [US2] Implement `save_metrics()` in `code/modeling/eval.py` to write initial metrics to `data/processed/metrics.json`

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for phylogenetic stratified split logic in `tests/unit/test_modeling.py`
- [X] T020 [P] [US2] Unit test for permutation baseline generation in `tests/unit/test_eval.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on BGC detection thresholds and generate the final report.

**Independent Test**: Re-run analysis with thresholds {0.1, 0.3, 0.5, 0.7} and verify R² variation is ≤ 0.05.

- [X] T030a [US3] Implement `retrain_with_thresholds()` in `code/modeling/eval.py` to re-train models using varied BGC detection thresholds. This task MUST invoke the modeling pipeline functions (T024/T023 logic) as a sub-routine with modified parameters, rather than re-implementing logic, to ensure consistent execution across the sweep.
- [X] T030b [US3] Implement `run_sensitivity_sweep()` in `code/modeling/eval.py` to iterate over thresholds and record R²/error rates for each sweep
- [X] T031 [US3] Implement `calculate_variation()` in `code/modeling/eval.py` to calculate the max R² difference across thresholds and write the metric to `metrics.json`.
- [X] T031b [US3] Implement `handle_sensitivity_failure()` in `code/modeling/eval.py` to check if variation > 0.05. If so, **raise a blocking VerificationError** immediately, halting the pipeline. This enforces Success Criterion SC-002 (variation ≤ 0.05) as a mandatory pass/fail condition, not a warning.
- [X] T032 [US3] Implement `generate_report()` in `code/cli/main.py` to compile model metrics, feature importance, and sensitivity results into a Markdown report at `data/processed/final_report.md`, including threshold justification text citing community standards (e.g., "antiSMASH default confidence").
- [X] T033 [US3] (Subsumed by T032) Ensure threshold justification text is included in the final report as per FR-008.
- [X] T034 [US3] Save final report as `data/processed/final_report.md` and `data/processed/sensitivity_results.json`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `README.md` Installation and Usage sections: Add specific instructions for installing antiSMASH dependencies and configuring API keys for NCBI/PMDB.
- [ ] T035b [P] Update `README.md` API Reference section: Add documentation for `code/data/download.py` and `code/modeling/train.py` functions.
- [ ] T036a [P] Refactor functions > 20 lines in `code/data/download.py` and `code/data/preprocess.py` to improve readability and testability.
- [ ] T036b [P] Refactor functions > 20 lines in `code/modeling/train.py` and `code/modeling/eval.py` to improve readability and testability.
- [ ] T037 Performance optimization: Ensure PCA is applied before PGLS if feature count > N
- [ ] T038 [P] Add unit tests for edge cases (zero BGCs, missing metabolites) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure all steps execute correctly on CI
- [X] T041 [US3] Implement `validate_report_compliance()` in `code/cli/main.py` to assert the final report contains all required sections (PGLS results, sensitivity sweep, threshold justification) before saving, ensuring FR-008 and SC-002 are met.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires aligned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model results from US2

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
Task: "Unit test for genome size filter logic in tests/unit/test_download.py"
Task: "Unit test for InChIKey harmonization in tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement download_genomes() in code/data/download.py"
Task: "Implement download_metabolites() in code/data/download.py"
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
- **CRITICAL DATA HYGIENE UPDATE**: T012 and T013 must be revised to strictly remove any `try/except` blocks that fallback to synthetic/mock data. If a real fetch fails for a specific species, that species is skipped with a warning, but the pipeline continues. **No secondary source fallbacks** are allowed to prevent silent data substitution.
- **REVISION**: T012 `download_genomes()` logic updated to remove Phytozome fallback. The task must now strictly adhere to the "FAIL LOUDLY" rule per species: if the primary configured source (NCBI RefSeq) fails for a species, skip it and log, do not attempt secondary sources.
- **REVISION**: T013 `download_metabolites()` logic updated to remove MetaboLights fallback. If the primary source fails for a species, skip it and log.
- **REVISION**: T017 `align_data()` updated to explicitly log the count of species excluded due to missing data, ensuring the alignment success rate (SC-004) is calculated against the original input list, not the filtered list.
- **REVISION**: T026 `run_phylogenetic_permutation()` updated to ensure the permutation strategy explicitly shuffles the *labels* (metabolite abundances) while keeping the *features* (BGCs) and the *phylogenetic tree* structure intact, and is scheduled to run **after** model training (T024) to enable valid comparison.
- **REVISION**: T032 `generate_report()` updated to include a specific section detailing the "Data Availability" which lists the exact number of species retrieved from each source and the number excluded, fulfilling the transparency requirement.
- **REVISION**: T012/T013 fallback logic clarified: Attempt Primary -> Skip on Failure (No Secondary). This satisfies the "FAIL LOUDLY" rule while allowing partial dataset construction.
- **REVISION**: T017b added to explicitly calculate and record alignment success rate in state file.
- **REVISION**: T023a-LOO/T023b conditional logic moved to T023a orchestrator, with explicit reference to `plan.md` Complexity Tracking for justification.
- **REVISION**: T031b updated to fail on sensitivity violation (raise error).
- **REVISION**: T027 updated to explicitly calculate and log p-value.
- **REVISION**: T007 updated to explicitly list derived output files (`aligned_matrix.csv`, `pca_features.csv`, `metrics.json`) for checksumming.
- **REVISION**: T024 updated to explicitly depend on T023a-PCA (PCA features).
- **REVISION**: T017 and T018 updated to explicitly preserve zero BGC count rows.