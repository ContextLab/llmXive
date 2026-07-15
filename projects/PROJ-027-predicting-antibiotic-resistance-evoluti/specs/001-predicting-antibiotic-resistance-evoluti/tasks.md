# Tasks: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Input**: Design documents from `/specs/001-predicting-antibiotic-resistance-evoluti/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a Create `code/01_ingest/`, `code/02_process/`, `code/03_model/`, `code/04_validate/`, `code/05_viz/` directories and verify directories exist
- [ ] T001b Create `utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/` directories
- [ ] T001c Create `tests/contract/` and `tests/unit/` directories with `.gitkeep` files

- [ ] T002 Initialize Python 3.11 project and create `code/requirements.txt` with `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`; verify installation with `pip check`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/logging.py` for standardized logging across the pipeline
- [X] T005 Implement `code/utils/config.py` to load paths, BioProject IDs, random seeds, and the `MAX_ISOLATES` limit (default a large sample size, CI limit 1000)
- [X] T006 Implement `code/utils/hash_artifacts.py` to compute SHA256 hashes for `data/` and `code/` and update `state/` JSON (Constitution Principle V)
- [~] T007 Create `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [~] T008 Create `tests/contract/` directory and stub schema validation helpers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download *E. coli* sequences and metadata, preprocess to identify SNPs/genes, and generate a structured feature matrix.

**Independent Test**: Run preprocessing on a small subset (N=50) and verify `data/processed/feature_matrix.csv` contains columns: `isolate_id`, `gene_presence_matrix`, `snp_counts`, `cnv_counts`, and `resistance_phenotype`.

### Blocking Prerequisites for US2 & US3

- [X] T019 [US1] Implement `code/02_process/generate_phylogeny.py` to infer a phylogenetic tree (Newick format) from the SNP data (output of T016) using `dendropy` for use in downstream validation (REQUIRED for US2/US3)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for feature matrix schema in `tests/contract/test_feature_matrix_schema.py`
- [~] T010 [P] [US1] Unit test for isolate filtering logic in `tests/unit/test_ingest.py` <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 3, column 1:
 1. **Basic filtering** - Verifie...
 ^
could not find expected ':'
 in "<unicode string>", line 4, column 1:
 2. **Missing value handling** -...
 ^) -->

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest/download_ncbi.py` to fetch FASTA sequences for specified BioProjects (e.g., PRJNA[Accession Number]) using NCBI E-utilities, enforcing the `MAX_ISOLATES` limit (A large-scale dataset for specification, with a subset reserved for continuous integration.)
- [X] T012 [US1] Implement `code/01_ingest/ingest_metadata.py` to parse susceptibility metadata, handle missing values, and log exclusion counts (Edge Case: missing metadata)
- [X] T013 [US1] Implement `code/01_ingest/download_card.py` to fetch resistance gene reference data
- [ ] T014 [US1] Implement `code/02_process/run_snippy.sh` wrapper to align sequences and call SNPs (CPU-limited, multiple threads) <!-- ATOMIZE: requested -->
- [X] T015 [US1] Implement `code/02_process/run_ariba.sh` wrapper to identify resistance genes
- [X] T016 [US1] Implement `code/02_process/build_feature_matrix.py` to aggregate SNPs, resistance gene presence, and **extract copy number variations (CNVs)** into a single CSV (Binary gene columns, Numeric SNP counts, Numeric CNV counts)
- [~] T017 [US1] Implement logic in `build_feature_matrix.py` to handle Edge Case: antibiotic classes with <50 isolates (exclude and log warning)
- [~] T018 [US1] Implement logic in `build_feature_matrix.py` to handle Edge Case: ALL classes have <50 isolates -> Abort execution with Error E004 and log message
- [~] T020 [US1] Add validation in `build_feature_matrix.py` to ensure no missing values in `resistance_phenotype` and row count matches isolate count

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including T019 tree generation)

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Logistic Regression and Random Forest models with mechanism-blind validation and Phylogenetically-Blocked CV.

**Independent Test**: Run training on a fixed seed subset; verify output models, confusion matrix, and AUC-ROC; confirm target resistance gene is excluded from features.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [~] T022 [P] [US2] Integration test for mechanism-blind filtering in `tests/integration/test_mechanism_blind.py`

### Implementation for User Story 2

- [X] T023a [US2] Implement `code/03_model/mechanism_blind_filter.py` to exclude known resistance genes for the target antibiotic class from the feature set (FR-008) using **CARD database categories** to map target class to genes
- [X] T023b [US2] Implement `code/03_model/split_data.py` to perform the **initial stratified split** of data into training, validation, and test sets as required by FR-003
- [X] T023c [US2] Implement `code/03_model/train_models.py` to train separate Logistic Regression (L1-regularized) and Random Forest models per antibiotic class (FR-009) using **Phylogenetically-Blocked CV** (split by clade ID from T019 tree) and consuming input from T023a (mechanism-blind filtered features)
- [ ] T024 [US2] Implement stratified cross-validation within `train_models.py` ensuring no data leakage (Strictly use Phylogenetically-Blocked CV logic as per plan)
- [ ] T025 [US2] Implement `code/03_model/evaluate.py` to calculate AUC-ROC, precision-recall curves, and confusion matrices on the held-out test set
- [ ] T026 [US2] Implement logic in `evaluate.py` to rank and export top genomic features (excluding target gene) to a summary table
- [ ] T027 [US2] Save trained model weights and evaluation metrics to `data/models/` with version hashes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform phylogenetically-aware permutation testing and sensitivity analysis to ensure scientific validity.

**Independent Test**: Run permutation on random data (p > 0.05 expected); run sensitivity sweep to verify metric variance across thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for permutation null distribution logic in `tests/unit/test_phyl_permutation.py`
- [ ] T029 [P] [US3] Integration test for sensitivity sweep output in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/validate/phylo_permutation.py` to perform phylogenetically-aware permutation testing. (PGLS residual permutation) respecting clonal lineages using the tree from T019
- [ ] T031 [US3] Implement logic in `phylo_permutation.py` to calculate p-value, **write p-value and significance flag to `data/processed/permutation_results.json`**, and **flag result as 'not significant' if p >= 0.05 without crashing the pipeline**
- [ ] T032 [US3] Implement `code/04_validate/sensitivity_analysis.py` to sweep classification thresholds across a range of values
- [ ] T033 [US3] Report false-positive and false-negative rate variations across thresholds in `sensitivity_analysis.py`
- [ ] T034 [US3] Implement `code/05_viz/generate_plots.py` to generate ROC curves, precision-recall curves, and feature importance bar plots using matplotlib/seaborn (FR-007)
- [ ] T035 [US3] Implement `code/main_reproducible.py` to re-execute the **full pipeline** (ingestion → processing → modeling → validation) from raw data to final figures, **verify W003 warning log and confirm feature set excludes plasmid features if data missing**, and verify checksums match, ensuring 'Single Source of Truth'

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` (README, quickstart)
- [ ] T037 Code cleanup and refactoring for CPU efficiency (batch processing)
- [ ] T038 Performance optimization: Ensure N=1000 isolate limit is strictly enforced in CI to meet -hour constraint while supporting N=5000 spec target
- [ ] T039 [P] Run `pytest` full suite and verify all contract tests pass
- [ ] T040 Run `hash_artifacts.py` to finalize `state/` and mark research complete

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Requires Feature Matrix from US1 and Phylogeny from T019 (Blocking Prerequisite)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Requires Trained Models from US2 and Phylogeny from T019 (Blocking Prerequisite)**

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
Task: "Contract test for feature matrix schema in tests/contract/test_feature_matrix_schema.py"
Task: "Unit test for isolate filtering logic in tests/unit/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement download_ncbi.py"
Task: "Implement ingest_metadata.py"
Task: "Implement download_card.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T019 for Phylogeny)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify feature matrix schema and tree generation)
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
 - Developer A: User Story 1 (Data Pipeline + Phylogeny)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
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
- **Compute Constraint**: All tasks must respect limited CPU resources, limited RAM, 6-hour limit. No GPU/CUDA. Use N=1000 for CI runs.
- **Phylogeny Requirement**: **T019 (Tree Generation) is a HARD PREREQUISITE** for T023c (Phylo-Blocked CV) and T030 (Permutation). T019 must be completed and validated before US2 or US3 can begin.
- **Significance Reporting**: T031 logs p-values and flags 'not significant' if p >= 0.05; it does NOT crash the pipeline. The pipeline continues to completion regardless of significance.
- **Reproducibility**: T035 runs the full pipeline from raw data to ensure 'Single Source of Truth' and verifies assumption handling (W003).