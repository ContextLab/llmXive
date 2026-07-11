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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw`, `data/processed`, `tests/`) <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python project with pinned dependencies (`scikit-learn`, `pandas`, `numpy`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`, `pymc3`, `tqdm`, `pydantic`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create Pydantic models for `Species`, `BGCFeature`, `Metabolite`, and `ModelOutput` in `code/models/`
- [X] T005 [P] Implement configuration loader in `code/config.py` to manage species lists, thresholds, and data paths
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` with file and console handlers
- [~] T007 Implement data directory structure creation and checksum verification logic in `code/data/__init__.py`
- [~] T008 Setup environment variable management for API keys (if needed) and local paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Alignment and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Automatically download genomic assemblies and metabolite tables, run antiSMASH, and generate an aligned matrix.

**Independent Test**: Execute the pipeline on a small subset (5 species) and verify the output CSV contains non-null values for both BGC counts and metabolite abundances, completing within 30 minutes on CPU.

### Implementation for User Story 1

- [~] T012 [US1] Implement `download_genomes()` in `code/data/download.py` to fetch FASTA/GFF from NCBI RefSeq/Phytozome, skipping genomes > 500MB, including retry logic, timeout handling, and graceful failure messaging for network timeouts
- [~] T013 [US1] Implement `download_metabolites()` in `code/data/download.py` to fetch abundance tables from PMDB/MetaboLights, including retry logic, timeout handling, and graceful failure messaging for network timeouts <!-- ATOMIZE: requested -->
- [~] T014 [US1] Implement `run_antiSMASH_wrapper()` in `code/data/preprocess.py` to execute the antiSMASH pipeline and parse JSON output to generate a binary presence matrix and a count matrix for BGC diversity
- [~] T016 [US1] Implement `harmonize_metabolites()` in `code/data/preprocess.py` to apply InChIKey normalization, pseudo-count +1, and log-transformation
- [~] T015 [US1] Implement `map_bgc_to_metabolite()` in `code/data/preprocess.py` using the MIBiG 3.0 ontology to map BGC types to metabolite classes, explicitly assigning to 'unknown' class if no match is found
- [~] T017 [US1] Implement `align_data()` in `code/data/align.py` to merge genomic and metabolomic data by species, filtering partial rows and logging warnings
- [ ] T018 [US1] Implement `save_aligned_matrix()` in `code/data/align.py` to write the final CSV to `data/processed/aligned_matrix.csv`
- [ ] T035a [US1] Implement `calculate_alignment_success_rate()` in `code/data/align.py` to calculate, log, and report the percentage of species with valid data (N≥5) for SC-004

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Unit test for genome size filter logic in `tests/unit/test_download.py`
- [ ] T010 [P] [US1] Unit test for InChIKey harmonization in `tests/unit/test_preprocess.py`
- [ ] T011 [P] [US1] Integration test for end-to-end data alignment on 3 mock species in `tests/integration/test_align.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train regression models (RF, Elastic Net, PGLS) with phylogenetic stratification and validate against a permutation baseline.

**Independent Test**: Run training on the P1 dataset, verify R² > 0 for PGLS, and confirm phylogenetic permutation baseline yields R² near zero.

- [ ] T021 [US2] Implement `load_phylogeny()` in `code/modeling/phylo.py` to load species tree data (Newick format) from `data/raw/phylogeny/` for stratification
- [ ] T021b [US2] Implement `construct_covariance_matrix()` in `code/modeling/phylo.py` using `dendropy` to generate the phylogenetic covariance matrix from the tree loaded in T021
- [ ] T024 [US2] [PRIMARY] Implement `train_pgls()` in `code/modeling/phylo.py` using `statsmodels` and the phylogenetic covariance matrix from T021b (constructed via `dendropy`) to account for non-independence. This task produces the PRIMARY analysis output per FR-010. Use PCA-reduced features from T023a-PCA.
- [ ] T024b [US2] Implement `report_primary_results()` in `code/modeling/eval.py` to explicitly extract, format, and log the PGLS R² and feature importance as the primary result for the final report, ensuring FR-010 compliance.
- [ ] T022 [US2] Implement `create_stratified_split()` in `code/modeling/train.py` to split data by phylogenetic clade
- [ ] T023a-PCA [US2] Implement `apply_pca()` in `code/modeling/train.py` to apply PCA for dimensionality reduction before multivariate modeling to prevent overfitting (N < 50 vs high features). Output saved to `data/interim/pca_features.csv`.
- [ ] T023a [US2] Implement `train_models_loo()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting using Leave-One-Out CV. **Run this task; if N >= 20, run T023b instead; otherwise skip T023b.** Use PCA-reduced features from T023a-PCA.
- [ ] T023b [US2] Implement `train_models_5fold()` in `code/modeling/train.py` to train Random Forest, Elastic Net, and Gradient Boosting with 5-fold CV. **Run only if N >= 20 (skip if N < 20).** Use PCA-reduced features from T023a-PCA.
- [ ] T025 [US2] Implement `evaluate_models()` in `code/modeling/eval.py` to calculate R² and Pearson correlation on hold-out sets
- [ ] T026 [US2] Implement `run_phylogenetic_permutation()` in `code/modeling/eval.py` to shuffle labels while preserving tree structure and calculate baseline R²
- [ ] T027 [US2] Implement `calculate_significance()` in `code/modeling/eval.py` to compare model R² against baseline (p < 0.05 check)
- [ ] T028 [US2] Implement `save_metrics()` in `code/modeling/eval.py` to write initial metrics to `data/processed/metrics.json`

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for phylogenetic stratified split logic in `tests/unit/test_modeling.py`
- [ ] T020 [P] [US2] Unit test for permutation baseline generation in `tests/unit/test_eval.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on BGC detection thresholds and generate the final report.

**Independent Test**: Re-run analysis with thresholds {0.1, 0.3, 0.5, 0.7} and verify R² variation is ≤ 0.05.

- [ ] T030a [US3] Implement `retrain_with_thresholds()` in `code/modeling/eval.py` to re-train models using varied BGC detection thresholds across a range of low to high values.
- [ ] T030b [US3] Implement `run_sensitivity_sweep()` in `code/modeling/eval.py` to iterate over thresholds and record R²/error rates for each sweep
- [ ] T031 [US3] Implement `calculate_variation()` in `code/modeling/eval.py` to calculate the max R² difference, return the metric, and write it to `metrics.json` (verify ≤ 0.05). **Run after T028; update metrics.json with variation result or FAIL flag if max_diff > 0.05.**
- [ ] T032 [US3] Implement `generate_report()` in `code/cli/main.py` or `code/utils/report.py` to compile model metrics, feature importance, and sensitivity results
- [ ] T033 [US3] Add threshold justification text to the report citing "antiSMASH default confidence" and community standards
- [ ] T034 [US3] Save final report as `data/processed/final_report.md` and `data/processed/sensitivity_results.json`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036 Code cleanup and refactoring of `code/data/` and `code/modeling/`
- [ ] T037 Performance optimization: Ensure PCA is applied before PGLS if feature count > N
- [ ] T038 [P] Add unit tests for edge cases (zero BGCs, missing metabolites) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure all steps execute correctly on CI

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