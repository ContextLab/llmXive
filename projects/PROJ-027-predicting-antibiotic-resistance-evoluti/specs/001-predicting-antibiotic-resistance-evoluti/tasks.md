# Tasks: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Input**: Design documents from `/specs/001-predicting-antibiotic-resistance-evolution/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001a Create `code/01_ingest/`, `code/02_process/`, `code/03_model/`, `code/04_validate/`, `code/05_viz/` directories and verify directories exist
- [X] T001b Create `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/` directories
- [X] T001c Create `tests/contract/` and `tests/unit/` directories with `.gitkeep` files

- [X] T002 Initialize Python 3.11 project and create `code/requirements.txt` with `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `biopython`, `requests`, `pyyaml`, `dendropy`, `statsmodels`; verify installation with `pip check`
- [X] T003a Create `.ruff.toml` with linting configuration for the project
- [X] T003b Create `pyproject.toml` with `[tool.black]` configuration for formatting

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/logging.py` for standardized logging across the pipeline
- [X] T005 Implement `code/utils/config.py` to load paths, BioProject IDs, random seeds, and configuration from `code/config.yaml`. **Required Keys**: `random_seed`, `max_isolates`, `permutation_iterations` (default 1000), `thresholds` (default [0.4, 0.45, 0.5, 0.55, 0.6]). **Verification**: Verify `config.yaml` exists and contains these keys.
- [X] T006 Implement `code/utils/hash_artifacts.py` to compute SHA256 hashes for `data/` and `code/` and update `state/` JSON (Constitution Principle V). **Note**: While the utility is implemented here, its *execution* is mandated at the end of US1, US2, and US3 via T040.
- [X] T007 Create `data/raw/` and `data/processed/` directory structure with `.gitkeep`
- [X] T008 Create `tests/contract/` directory and stub schema validation helpers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download *E. coli* sequences and metadata, preprocess to identify SNPs/genes, and generate a structured feature matrix.

**Independent Test**: Run preprocessing on a small subset (N=50) and verify `data/processed/feature_matrix.csv` contains columns: `isolate_id`, `gene_presence_matrix`, `snp_counts`, `cnv_counts`, and `resistance_phenotype`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for feature matrix schema in `tests/contract/test_feature_matrix_schema.py`
- [X] T010 [P] [US1] Unit test for isolate filtering logic in `tests/unit/test_ingest.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest/download_ncbi.py` to fetch FASTA sequences for specified BioProjects (e.g., PRJNA[Accession Number]) using NCBI E-utilities, enforcing the `MAX_ISOLATES` limit (A large-scale dataset for specification, with a subset reserved for continuous integration.)
- [X] T012 [US1] Implement `code/01_ingest/ingest_metadata.py` to parse susceptibility metadata, handle missing values, and log exclusion counts (Edge Case: missing metadata). **Logging**: If plasmid data is missing, log warning **W003** ("Plasmid data missing; proceeding with chromosomal features only").
- [X] T013 [US1] Implement `code/01_ingest/download_card.py` to fetch resistance gene reference data
- [X] T014 [US1] Implement `code/02_process/run_snippy.sh` wrapper to align sequences and call SNPs (CPU-limited, multiple threads). **Verification**: Verify VCF exists and contains >0 variants for each processed isolate.
- [X] T015 [US1] Implement `code/02_process/run_ariba.sh` wrapper to identify resistance genes
- [X] T016 [US1] Implement `code/02_process/build_feature_matrix.py` to aggregate SNPs, resistance gene presence, and **extract copy number variations (CNVs)** into a single CSV. **CNV Logic**: Parse ARIBA output files to extract **coverage depth** as a proxy for copy number counts for each resistance gene; if coverage depth is missing, default to 1 or 0 based on presence. **Logging**: If plasmid data is missing, log warning **W003**. **Output**: Binary gene columns, Numeric SNP counts, Numeric CNV counts (proxy). **Edge Cases**: 
  1. If an antibiotic class has <50 isolates, exclude it and log warning **W005** ("Antibiotic class X has <50 isolates; excluding"). 
  2. If the count of excluded classes equals the total number of classes, raise Error **E004** ("Insufficient data for any class") and abort execution.
  **Validation**: Ensure no missing values in `resistance_phenotype`, row count matches isolate count, and verify presence of `cnv_counts` columns.
- [X] T019 [US1] [Depends: T014] Implement `code/02_process/generate_phylogeny.py` to infer a phylogenetic tree (Newick format) from the SNP data (output of T014) using `dendropy` for use in downstream validation. **Required for US2/US3 Phylogenetic Blocking** (generates input for T023c and T030). Output: `data/processed/phylogeny.nwk`. **Verification**: Verify `phylogeny.nwk` exists and is valid Newick format.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including T019 tree generation)

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Logistic Regression and Random Forest models with mechanism-blind validation and Phylogenetically-Blocked CV.

**Independent Test**: Run training on a fixed seed subset; verify output models, confusion matrix, and AUC-ROC; confirm target resistance gene is excluded from features.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T022 [P] [US2] Integration test for mechanism-blind filtering in `tests/integration/test_mechanism_blind.py`

### Implementation for User Story 2

- [X] T023b [US2] [Depends: T013] Implement `code/03_model/generate_class_gene_mapping.py` to parse CARD JSON data (`data/raw/card.json`) and create a mapping file `data/processed/class_to_genes.json` that maps each antibiotic class to its canonical resistance genes. **Logic**: Iterate CARD AMR detection models, extract `drug_class` and `gene` fields, and aggregate into a dictionary. **Verification**: Verify JSON file exists and contains entries for all target classes.
- [X] T023a [US2] Implement `code/03_model/mechanism_blind_filter.py` to exclude known resistance genes for the target antibiotic class from the feature set (FR-008) using the mapping generated by T023b (`data/processed/class_to_genes.json`).
- [X] T023c [US2] Implement `code/03_model/split_data.py` to perform the **Phylogenetically-Blocked Splitting** of data. **Logic**: Read the phylogenetic tree from T019 (`data/processed/phylogeny.nwk`), group isolates by clade, and split the dataset by clade (not by random isolate) to prevent data leakage. Ensure the split is stratified by resistance phenotype *within* each clade block. **Verification**: Verify no clade appears in both training and test sets.
- [X] T023d [US2] [Depends: T019] Implement `code/03_model/train_models.py` to train separate Logistic Regression (L1-regularized) and Random Forest models per antibiotic class (FR-009). **Logic**: Iterate over **every unique antibiotic class** in the dataset; for each class, train a distinct LR and RF model instance using the mechanism-blind filtered features (from T023a) and the phylogenetically-blocked split (from T023c). **Naming Convention**: Save distinct model files using the pattern `model_{type}_{class}.pkl` (e.g., `model_lr_ciprofloxacin.pkl`) to `data/models/` to prevent file collisions. **Verification**: Verify distinct model files exist for each class and that the target resistance gene is excluded from features.
- [X] T025 [US2] Implement `code/03_model/evaluate.py` to calculate AUC-ROC, precision-recall curves, and confusion matrices on the held-out test set
- [X] T026 [US2] Implement logic in `evaluate.py` to rank and export top genomic features (excluding target gene) to a summary table. **Output**: Write `feature_ranking.csv` to `data/processed/` with top genomic features.
- [X] T027 [US2] Save trained model weights and evaluation metrics to `data/models/` with version hashes. **Output**: Save `model_lr.pkl`, `model_rf.pkl`, and `metrics.json` to `data/models/`. **Verification**: Verify files exist and load successfully.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform phylogenetically-aware permutation testing and sensitivity analysis to ensure scientific validity.

**Independent Test**: Run permutation on random data (p > 0.05 expected); run sensitivity sweep to verify metric variance across thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for permutation null distribution logic in `tests/unit/test_phyl_permutation.py`
- [X] T029 [P] [US3] Integration test for sensitivity sweep output in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [X] T030 [US3] [Depends: T019] Implement `code/04_validate/phylo_permutation.py` to perform phylogenetically-aware permutation testing. (PGLS residual permutation) respecting clonal lineages using the tree from T019. **Config**: **Hardcode** `permutation_iterations = 1000` to satisfy FR-005/SC-002. Ignore or reject any config value; if a config value is present and not exactly 1000, raise an error. **Logging**: Log **W005** if <50 isolates found for a class; log **W003** if plasmid data is missing.
- [X] T031 [US3] Implement logic in `phylo_permutation.py` to calculate p-value, **write p-value and significance flag to `data/processed/permutation_results.json`**, and **flag result as 'not significant' if p >= 0.05 without crashing the pipeline**. **Blocking**: If p >= 0.05, the pipeline must set a flag that **blocks** the generation of any final report or paper claiming significance. **Verification**: Verify `data/processed/permutation_results.json` exists and contains keys `p_value` and `significant_flag`.
- [X] T032 [US3] Implement `code/04_validate/sensitivity_analysis.py` to sweep classification thresholds across the **exact set {0.4, 0.45, 0.5, 0.55, 0.6}** as required by FR-006 and SC-003. **Config**: Read `thresholds` from `code/utils/config.py` if present, but **strictly validate** that the set matches {0.4, 0.45, 0.5, 0.55, 0.6} exactly; raise an error if it deviates.
- [X] T033 [US3] Implement logic in `sensitivity_analysis.py` to report false-positive and false-negative rate variations across the **specific thresholds {0.4, 0.45, 0.5, 0.55, 0.6}**. **Output**: Write `sensitivity_sweep.csv` to `data/processed/` containing `threshold`, `FP_rate`, `FN_rate` columns. **Metric**: **Calculate and export the range of variation** (max FP_rate - min FP_rate) as a summary field in the output to satisfy SC-003.
- [X] T034 [US3] Implement `code/05_viz/generate_plots.py` to generate ROC curves, precision-recall curves, and feature importance bar plots using matplotlib/seaborn (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Mandatory Gates

**Purpose**: Enforce Mandatory Gates defined in plan.md (Contract Validation and Versioning)

- [X] T039 [P] **MANDATORY GATE**: Run `pytest` full suite (unit, contract, integration) and verify all tests pass. Log results to `data/processed/test_results.log`. **Verification**: Ensure exit code is 0 and all contract tests pass.
- [X] T040 [P] **MANDATORY GATE**: Run `hash_artifacts.py` to finalize `state/` and mark research complete. **Verification**: Verify `state/` JSON files are updated with new artifact hashes and timestamps.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Implement `code/main_reproducible.py` to re-execute the **full pipeline** (ingestion → processing → modeling → validation) from raw data to final figures. **Verification**: Verify `data/processed/feature_matrix.csv`, `data/models/*.pkl`, and figures exist; verify checksums match; **verify W003 warning log** ("Plasmid data missing; proceeding with chromosomal features only") is present if plasmid data is missing by checking the log file content; confirm feature set excludes plasmid features if data missing. **Dependencies**: Must run after T027 and T034.
- [X] T036 [P] Documentation updates in `docs/` (README, quickstart)
- [X] T037 Code cleanup and refactoring for CPU efficiency (batch processing)
- [X] T038 Performance optimization: Ensure N=1000 isolate limit is strictly enforced in CI to meet -hour constraint while supporting N=5000 spec target
- [X] T041 [US1] Implement robust error handling in `code/01_ingest/download_ncbi.py` to ensure **FAIL LOUDLY** behavior on real data fetch failure, removing any `try/except` blocks that fallback to synthetic/mock data generation.
- [X] T042 [US1] Add explicit validation in `code/02_process/build_feature_matrix.py` to verify that the input FASTA files exist and are non-empty before attempting Snippy/ARIBA processing, raising an explicit error if raw data is missing.
- [X] T043 [US2] Logic for Phylogenetically-Blocked Splitting has been moved to T023c. No separate implementation required.
- [X] T044 [US3] Add a pre-check in `code/04_validate/phylo_permutation.py` to verify the input tree (T019) is rooted and contains all isolate IDs present in the feature matrix, failing early if topology mismatches data.
- [X] T045 [US3] Ensure `code/04_validate/sensitivity_analysis.py` logs the exact threshold values used and the resulting metrics in a machine-readable format (JSON) in addition to the CSV, to facilitate automated verification of the {0.4, 0.45, 0.5, 0.55, 0.6} set.
- [X] T046 [P] **Scalability Validation**: Implement a streaming/stress test in `code/utils/stress_test.py` to verify the pipeline can handle the spec-mandated **N=5000** isolates without OOM or timeout, using `datasets.load_dataset(..., streaming=True)` to process in chunks. **Verification**: Verify the test completes successfully with N=5000 (or a representative streamed sample) and logs the memory usage profile.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: 
  - User Story 1 (US1) depends on Foundational (Phase 2).
  - **User Story 2 (US2) and User Story 3 (US3) depend on the completion of User Story 1 (specifically T019 and T016).**
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation & Gates (Phase 6)**: Depends on all User Stories completion
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
- **Compute Constraint**: All tasks must respect limited CPU resources, limited RAM, -hour limit. No GPU/CUDA. Use N=1000 for CI runs.
- **Phylogeny Requirement**: **T019 (Tree Generation) is a HARD PREREQUISITE** for T023c (Phylo-Blocked CV) and T030 (Permutation). T019 must be completed and validated before US2 or US3 can begin. T019 is now correctly placed in Phase 3 (US1) to ensure data availability.
- **Significance Reporting**: T031 logs p-values and flags 'not significant' if p >= 0.05; it does NOT crash the pipeline. The pipeline continues to completion regardless of significance, but T031 now includes logic to **block** final reporting if significance is not met.
- **Reproducibility**: T035 runs the full pipeline from raw data to ensure 'Single Source of Truth' and verifies assumption handling (W003).
- **Threshold Compliance**: T032 and T033 explicitly enforce the {0.4, 0.45, 0.5, 0.55, 0.6} set with strict validation.
- **CNV Extraction**: T016 explicitly implements CNV extraction using ARIBA coverage depth as a proxy.
- **Warning Codes**: W005 for <50 isolates; W003 for plasmid data missing.
- **Data Integrity**: T041 and T042 enforce strict "Fail Loudly" on data ingestion to prevent synthetic data fallback.
- **Leakage Prevention**: T023c now explicitly implements Phylogenetically-Blocked Splitting.
- **Iteration Enforcement**: T030 enforces a hard value of 1000 (no configuration override).
- **Class Iteration**: T023d explicitly iterates over all classes to train distinct models with a defined naming convention.
- **Variation Metric**: T033 calculates and exports the range of variation for FP rates.
- **Mandatory Gates**: T039 (pytest) and T040 (hashing) are now completed tasks in Phase 6, enforcing the plan's workflow constraints.
- **Scalability**: T046 explicitly validates the 5000 isolate capacity via streaming.