---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Input**: Design documents from `/specs/001-predict-plant-metabolite-profiles/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001a Create `code/` directory: `mkdir -p code`
- [ ] T001b Create `tests/` directory: `mkdir -p tests/unit tests/integration tests/contract`
- [ ] T001c Create `data/` directory: `mkdir -p data/raw data/processed data/interim`
- [X] T001d Initialize Python package files: `touch code/__init__.py code/data/__init__.py code/modeling/__init__.py code/utils/__init__.py code/cli/__init__.py tests/__init__.py`
- [ ] T001e Verify directory structure: Run `tree code tests data` (or equivalent) to generate a file tree log in `data/raw/.verification/directory_tree.log` to satisfy Constitution Principle I (Reproducibility) before code is written.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create Pydantic models for `Species` (fields: name, clade, genome_path, metabolite_path), `BGCFeature` (fields: type, presence, count, metabolite_class), `Metabolite` (fields: inchinkey, abundance, class), and `ModelOutput` (fields: model_type, r2, feature_importance) in `code/models/`
- [X] T005 [P] Implement configuration loader in `code/config.py` to manage species lists, thresholds, and data paths
- [X] T005b [P] Implement `seed_manager` in `code/config.py` to set and retrieve global random seeds for reproducibility (Constitution Principle I); update T023a, T023b, T024, T026 to use `config.seed_manager.get_seed()`.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and console handlers
- [X] T007 Implement `verify_and_write_checksums()` in `code/data/__init__.py` to: 1) calculate MD5/SHA256 for all files in `data/raw`, 2) write the checksums to `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` under `artifact_hashes`, and 3) raise an error if any file is missing or checksum mismatch occurs. **This task MUST be called immediately by T012c and T013c after successful data download to satisfy Constitution Principle III (Data Hygiene).**
- [X] T008 Create `.env.example` with keys `NCBI_API_KEY`, `PMDB_TOKEN` and update `code/config.py` to load these from environment variables
- [X] T040 [US2] Implement `load_phylogeny_source()` in `code/data/download.py` to fetch the species phylogeny (Newick format) from a verified source (e.g., Open Tree of Life API) or fallback to `data/raw/phylogeny/tree.nwk` if available, ensuring T021 has valid input. **Moved to Foundational to ensure US1 independence and US2 readiness.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Alignment and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Automatically download genomic assemblies and metabolite tables, run antiSMASH, and generate an aligned matrix.

**Independent Test**: Execute the pipeline on a small subset (5 species) and verify the output CSV contains non-null values for both BGC counts and metabolite abundances, completing within 30 minutes on CPU.

### Implementation for User Story 1

- [X] T012a Implement `download_from_refseq()` in `code/data/download.py` to fetch FASTA/GFF from NCBI RefSeq, including retry logic and timeout handling
- [X] T012b Implement `check_genome_size()` in `code/data/download.py` to accept a `source` argument ('refseq' or 'phytozome'). If 'refseq', use HEAD request; if 'phytozome', fetch metadata JSON to extract genome size. Raise an error if size > 500MB.
- [X] T012c [US1] Implement `download_genomes()` in `code/data/download.py` to orchestrate T012a/T012b. Logic: 1) Try RefSeq. **Before attempting download, call `check_genome_size('refseq')`.** 2) If RefSeq fails (404, timeout, 500) or size > 500MB, **log the specific failure reason for RefSeq**, then **Call `check_genome_size('phytozome')`** before attempting Phytozome. 3) If Phytozome fails or size > 500MB, **log the specific failure reason for Phytozome**. 4) If all sources fail or are size-restricted, raise `DataFetchError` with a clear message indicating the specific source and failure reason for *each* attempt. **Upon successful download, immediately call T007 to checksum the new file.**
- [X] T013a Implement `download_from_pmdb()` in `code/data/download.py` to fetch abundance tables from PMDB, including retry logic and timeout handling
- [X] T013b Implement `download_from_metabolights()` in `code/data/download.py` to fetch abundance tables from MetaboLights, including retry logic and timeout handling
- [X] T013c Implement `download_metabolites()` in `code/data/download.py` to orchestrate T013a/T013b. Logic: 1) Try PMDB. If 404, timeout, or 500 error, **log specific failure**, attempt MetaboLights. 2) If all sources fail, **log specific failure for each**, raise `DataFetchError`. **Upon successful download, immediately call T007 to checksum the new file.**
- [X] T014 [US1] Implement `run_antiSMASH_wrapper()` in `code/data/preprocess.py` to: 1) Verify antiSMASH is in PATH, 2) Execute antiSMASH with default command-line arguments on each genome. **If execution fails (timeout/OOM), log a clear error message including the species name and error type, and exclude the species from the dataset rather than failing the entire pipeline (fail gracefully per spec Edge Cases).** 3) **Parse the JSON output** to generate a binary presence matrix and a count matrix for BGC diversity. **Implementation must include explicit JSON parsing logic (e.g., `json.load`) and error handling for malformed JSON.**
- [X] T016 [US1] Implement `harmonize_metabolites()` in `code/data/preprocess.py` to apply InChIKey normalization, pseudo-count +1, and log-transformation
- [X] T015 [US1] Implement `map_bgc_to_metabolite()` in `code/data/preprocess.py` using the MIBiG ontology to map BGC types to metabolite classes, explicitly assigning to 'unknown' class if no match is found
- [X] T017 [US1] Implement `align_data()` in `code/data/align.py` to merge genomic and metabolomic data by species, filtering partial rows and logging warnings
- [X] T018 [US1] Implement `save_aligned_matrix()` in `code/data/align.py` to write the final CSV to `data/processed/aligned_matrix.csv`
- [X] T035a [US1] Implement `calculate_alignment_success_rate()` in `code/data/align.py` to calculate, log, and report the percentage of species with valid data (N≥5) for SC-004
- [X] T035b [US1] Implement `log_alignment_metrics()` in `code/data/align.py` to write the alignment success rate to `data/processed/metrics.json` under the key `alignment_success_rate` for SC-004 verification

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train regression models (RF, Elastic Net, PGLS) with phylogenetic stratification and validate against a permutation baseline.

**Independent Test**: Run training on the P1 dataset, verify R² > 0 for PGLS, and confirm phylogenetic permutation baseline yields R² near zero.

- [X] T021 [US2] Implement `load_phylogeny()` in `code/modeling/phylo.py` to load species tree data (Newick format) from `data/raw/phylogeny/` for stratification
- [X] T021b [US2] Implement `construct_covariance_matrix()` in `code/modeling/phylo.py` using `dendropy` to generate the phylogenetic covariance matrix from the tree loaded in T021. **Dependency: T021 must complete first.**
- [X] T023a_pca [US2] Implement `apply_pca()` in `code/modeling/train.py` to apply PCA for dimensionality reduction before multivariate modeling to prevent overfitting (N < 50 vs high features). Output saved to `data/interim/pca_features.csv`. **Must run before T023a, T023b, and T024.**
- [X] T023c [US2] Implement `select_cv_method()` in `code/modeling/train.py` to **parse `data/processed/aligned_matrix.csv` to calculate N (number of species)**, then automatically select between T023a (LOO if N < 20) and T023b (5-fold if N >= 20).
- [X] T023a [US2] Implement `train_models_loo()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting using Leave-One-Out CV. **Run this task if N < 20.** Use PCA-reduced features from `data/interim/pca_features.csv`. **Must explicitly use `config.seed_manager.get_seed()` for reproducibility.**
- [X] T023b [US2] Implement `train_models_5fold()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting with k-fold cross-validation. **Run only if N >= 20 (skip if N < 20).** Use PCA-reduced features from `data/interim/pca_features.csv`. **Must explicitly use `config.seed_manager.get_seed()` for reproducibility.**
- [X] T023d [US2] Implement `document_cv_deviation()` in `code/modeling/train.py` or `docs/` to explicitly document the justification for deviating from FR-005's "k-fold" requirement when N < 20, linking to the "Complexity Tracking" rationale in `plan.md`. **This task ensures traceability for the LOO vs. k-fold decision.**
- [X] T024 [US2] [PRIMARY] Implement `train_pgls()` in `code/modeling/phylo.py` using `statsmodels` and the phylogenetic covariance matrix from T021b (constructed via `dendropy`) to account for non-independence. This task produces the PRIMARY analysis output per FR-010. Use PCA-reduced features from `data/interim/pca_features.csv`. **Must explicitly use `config.seed_manager.get_seed()` for reproducibility.**
- [X] T024c [US2] Implement `verify_primary_model()` in `code/modeling/eval.py` to explicitly mark PGLS as the "primary" model and RF/ElasticNet/GB as "secondary/exploratory" in the code and `metrics.json` metadata, ensuring FR-010 compliance before reporting. **Must run before T024b.**
- [X] T024b [US2] [PRIMARY] Implement `report_primary_pgls_results()` in `code/modeling/eval.py` to extract, format, and write the PGLS R² and feature importance to `data/processed/primary_results.json`. **Must run after T024c.**
- [X] T022 [US2] Implement `create_stratified_split()` in `code/modeling/train.py` to split data by phylogenetic clade
- [X] T025 [US2] Implement `evaluate_models()` in `code/modeling/eval.py` to calculate R² and Pearson correlation on hold-out sets
- [X] T026 [US2] Implement `run_phylogenetic_permutation()` in `code/modeling/eval.py` to shuffle labels while preserving tree structure, calculate baseline R² for each iteration, and output a `baseline_r2_distribution` array. **Must explicitly use `config.seed_manager.get_seed()` for reproducibility.**
- [X] T027a [US2] Implement `perform_pvalue_test()` in `code/modeling/eval.py` to compare model R² against the `baseline_r2_distribution` from T026, calculate p-value (p < 0.05), and write the result to `data/processed/metrics.json`.
- [X] T027 [US2] Implement `calculate_significance()` in `code/modeling/eval.py` to orchestrate T027a and report the final significance status
- [X] T028 [US2] Implement `save_metrics()` in `code/modeling/eval.py` to write initial metrics to `data/processed/metrics.json`

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for phylogenetic stratified split logic in `tests/unit/test_modeling.py`
- [X] T020 [P] [US2] Unit test for permutation baseline generation in `tests/unit/test_eval.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on BGC detection thresholds and generate the final report.

**Independent Test**: Re-run analysis with thresholds {0.1, 0.3, 0.5, 0.7} and verify R² variation is ≤ 0.05.

- [X] T030a [US3] Implement `retrain_with_thresholds()` in `code/modeling/eval.py` to **re-run the FULL pipeline (T014 antiSMASH parsing -> T016 harmonization -> T017 alignment -> T023a_pca PCA)** for each BGC detection threshold value (input: float threshold). **CRITICAL: Do NOT use cached PCA features from previous runs; regenerate the feature matrix for each threshold to ensure the sweep is mathematically valid.** The task must call the antiSMASH parsing logic (T014) with the new threshold, generate a fresh BGC count matrix, re-align, and re-apply PCA before training. Output: retrained model metrics for each threshold.
- [X] T030b [US3] Implement `run_sensitivity_sweep()` in `code/modeling/eval.py` to iterate over thresholds and record R²/error rates for each sweep
- [X] T031 [US3] Implement `calculate_variation()` in `code/modeling/eval.py` to calculate the max R² difference from T030b, return the metric, and write it to `metrics.json` (verify ≤ 0.05). **Run after T030b; update metrics.json with variation result or FAIL flag if max_diff > 0.05.**
- [X] T032 [US3] Implement `generate_report()` in `code/cli/main.py` or `code/utils/report.py` to compile model metrics, feature importance, and sensitivity results; save to `data/processed/final_report.md`
- [X] T033 [US3] Implement `add_threshold_justification()` in `code/cli/main.py` or `code/utils/report.py` to append threshold justification text citing "antiSMASH default confidence" and community standards to `data/processed/final_report.md` under section "Threshold Justification"
- [X] T034 [US3] Save final report as `data/processed/final_report.md` and `data/processed/sensitivity_results.json`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `README.md` (CLI usage examples) and `docs/` (pipeline architecture); verify via `quickstart.md` validation.
- [ ] T036 Code cleanup and refactoring of `code/data/` and `code/modeling/`
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