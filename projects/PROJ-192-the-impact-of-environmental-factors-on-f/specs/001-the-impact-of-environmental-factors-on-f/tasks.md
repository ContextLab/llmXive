# Tasks: Impact of Environmental Factors on Fungal Community Structure in Soil

**Input**: Design documents from `/specs/001-impact-of-environmental-factors/`
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

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `results/`)
- [X] T002 Initialize Python project with `requirements.txt` (pandas, scikit-learn, scipy, skbio, miceforest, pyyaml, dask, matplotlib, seaborn)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes memory safety checks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `src/models/schemas.py` with Pydantic models
 - [ ] T004a [P] Implement ASV Table schema (sample_id, asv_id, count)
 - [ ] T004b [P] Implement Environmental Matrix schema (sample_id, pH, nutrients, etc.)
 - [ ] T004c [P] Implement Results schema (R2, p-value, p-value_adj)
- [X] T005 [P] Implement `src/utils/logging.py` and `src/utils/checksums.py`
 - [ ] T005a [P] Implement structured JSON logging in `src/utils/logging.py`
 - [ ] T005b [P] Implement SHA256 verification in `src/utils/checksums.py`
- [X] T006 [P] Setup `src/config/constants.yaml` with thresholds (VIF>5, p<0.05, min_samples=10, max_ram=7GB)
- [ ] T007 [P] Implement data ingestion logic in `src/pipelines/ingest.py`
 - [ ] T007a [P] Implement validation logic for downloaded files (checksum verification, format check). **Constraint**: Do NOT use `datasets.load_dataset` for raw sequence data; this function typically returns processed tables which violates the requirement for raw FASTQ ingestion.
 - [ ] T007b [P] Implement metadata harmonization logic.
- [ ] T008 Configure `src/cli/main.py` entry point with argument parsing for `--mode` (validation vs research) and `--stratify-by`
- [ ] T014a [P] [US1] Implement memory-safe subsampling logic in `src/utils/memory.py` to trigger subsampling if RAM > 6GB (FR-009).
- [ ] T014b [US1] Implement **Memory Projection Logic** in `src/pipelines/ingest.py`: Calculate estimated peak RAM usage based on sample count and read depth *before* loading data. If `estimated_peak_ram > 6GB`, trigger subsampling (T014a) and log the ratio. This must occur BEFORE MICE or VIF steps.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Environmental-Community Association Analysis (Priority: P1) 🎯 MVP

**Goal**: Ingest public ITS data, harmonize metadata, compute diversity, and run PERMANOVA/db-RDA to identify significant abiotic drivers.

**Independent Test**: The workflow executes on a subset of public datasets and outputs `results/permanova_summary.csv` with significant correlations and `results/db_rda_variance.csv`.

### Pre-Implementation: Tests for User Story 1 (MUST WRITE FIRST) ⚠️

> **NOTE**: These tasks are to **WRITE** the test code first (TDD). They cannot be *executed* until the implementation code exists.

- [ ] T010 [P] [US1] **Write** contract test for ASV table schema validation in `tests/contract/test_asv_schema.py` (Verify failure on invalid schema).
- [ ] T011 [P] [US1] **Write** contract test for environmental metadata schema in `tests/contract/test_metadata_schema.py` (Verify failure on missing columns).
- [~] T012 [P] [US1] **Write** integration test for end-to-end pipeline on synthetic data in `tests/integration/test_workflow_us1.py` (Verify failure on missing implementation).

### Implementation for User Story 1

- [~] T013a [US1] Implement download logic in `src/pipelines/ingest.py` to fetch **RAW FASTQ files** (.fastq.gz) from SRA/IMG/M. **Constraint**: Must use direct HTTP fetch or `sra-tools` to retrieve raw reads. **Deliverable**: Save files to `data/raw-seq/<dataset_id>.fastq.gz` and generate SHA256 checksum. Do NOT use `datasets.load_dataset` for raw sequence data. <!-- FAILED: unspecified -->
- [~] T013b [US1] Implement validation logic in `src/pipelines/ingest.py` to exclude datasets missing required columns (pH, nutrients, etc.) and verify checksums against `data/raw-seq/`.
- [~] T013c [US1] Implement DADA2/QIIME2 denoising pipeline in `src/pipelines/preprocess.py` to process **RAW FASTQs** (from T013a) into ASV tables. <!-- FAILED: unspecified -->
 - [ ] T013c1 [US1] Implement quality filtering and primer trimming.
 - [ ] T013c2 [US1] Implement error model learning and denoising.
 - [ ] T013c3 [US1] Implement read merging and chimera removal.
 - [ ] T013c4 [US1] Output ASV table to `data/qc/asv_table.tsv`.
- [~] T013d [US1] Implement construction and validation of Environmental Matrix in `src/pipelines/ingest.py` by merging and cleaning metadata; output `data/metadata/harmonized_matrix.csv`.
- [~] T014 [US1] Implement ontology mapping in `src/pipelines/ingest.py` to standardize biome labels (e.g., 'Temperate Forest' -> 'Forest').
- [~] T015 [US1] Implement MICE imputation in `src/pipelines/preprocess.py` using `miceforest` with a configured iteration limit. Check convergence flag; if False, log warning and drop rows; verify `data/cleaned_metadata.csv` has no NaNs (FR-008).
- [~] T016 [US1] Implement VIF calculation in `src/pipelines/preprocess.py`; remove or PCA-combine variables with VIF > 5 (FR-007, Edge Cases). **Input**: Imputed data from T015.
- [~] T017 [US1] Implement beta-diversity (Bray-Curtis) and alpha-diversity (Shannon, Observed ASVs) calculation in `src/pipelines/preprocess.py` using `skbio`; **Output**: Bray-Curtis distance matrix and Euclidean distance matrix (FR-002).
- [~] T018 [US1] Implement PERMANOVA (adonis2) with ≥999 permutations and Benjamini-Hochberg FDR correction in `src/pipelines/analysis.py`. **Conditional Logic**: If sample size < 20, use **exact permutation test** or **≥9999 permutations** (FR-003). **Input**: Distance matrices from T017; **Output**: `results/permanova_summary.csv` with columns: term, R2, p-value, p-value_adj.
- [~] T019 [US1] Implement variance partitioning (varpart) to quantify unique/shared variance by predictor in `src/pipelines/analysis.py` (FR-004).
- [~] T020 [US1] Implement db-RDA triplot generation in `src/pipelines/report.py` showing sample clustering by dominant vector. <!-- ATOMIZE: requested -->
- [~] T022 [US1] Generate `results/permanova_summary.csv` and `results/db_rda_variance.csv` with FDR-corrected p-values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Biome-Specific Driver Ranking (Priority: P2)

**Goal**: Stratify analysis by biome/soil type and re-run tests to identify context-specific driver rankings.

**Independent Test**: The workflow runs with `--stratify-by=biome` and generates separate summary tables and plots for each biome.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US2] Contract test for biome-stratified results schema in `tests/contract/test_biome_results_schema.py`
- [~] T024 [P] [US2] Integration test for skipping strata with < 10 samples in `tests/integration/test_stratification.py`

### Implementation for User Story 2

- [~] T025 [US2] Implement stratification logic in `src/pipelines/analysis.py` to split cleaned data by `biome` column (using output from T013d).
- [~] T026 [US2] Implement power check in `src/pipelines/analysis.py`: If stratum sample count < 10, **SKIP** execution of PERMANOVA/varpart for that stratum, log error to `results/skipped_strata.log`, and proceed; verify log file contains biome name (FR-005).
- [~] T027 [US2] Re-run PERMANOVA and varpart for each valid stratum in `src/pipelines/analysis.py`.
- [~] T028 [US2] Generate `results/db_rda_biome_<NAME>.csv` for each biome with R² values.
- [~] T029 [US2] Implement logic to determine top driver per biome. **Metric**: Calculate **standard deviation of the rank index** of the top driver across biomes. **Pass Condition**: Verify standard deviation ≤ 0.5 (SC-003). **Deliverable**: Log the calculated standard deviation and a Pass/Fail flag to `results/biome_ranking_summary.csv`.
- [~] T030 [US2] Generate summary report indicating if top predictor changes across biomes (e.g., pH in forests, moisture in grasslands).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity and Robustness Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on p-value and R² thresholds to assess the stability of the dominant driver ranking.

**Independent Test**: The workflow runs with `--sweep-thresholds` and outputs `results/sensitivity_analysis.csv` showing driver stability.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T031 [P] [US3] Contract test for sensitivity analysis schema in `tests/contract/test_sensitivity_schema.py`
- [~] T032 [P] [US3] Unit test for robustness flagging logic in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [~] T033 [US3] Implement threshold sweep logic in `src/pipelines/report.py` to iterate p-values across conventional significance thresholds and R² cutoffs across a range of explanatory power benchmarks.
- [~] T034 [US3] Re-evaluate top driver ranking for each threshold combination.
- [~] T035 [US3] Generate `results/sensitivity_analysis.csv` documenting top driver per threshold set. <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 6, column 1:
 **File**: `code/src/pipelines/re...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 6, column 2:
 **File**: `code/src/pipelines/rep...
 ^) -->
- [~] T036 [US3] Implement robustness metric calculation: Count rows in `sensitivity_analysis.csv` where top_driver is stable; calculate percentage against total rows; flag Pass if ≥ 80%, Fail otherwise (SC-004).
- [~] T037 [US3] Generate `results/robustness_summary.md` stating the percentage and Pass/Fail status against the 80% threshold.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Generate `results/sampling_report.csv` documenting subsampling ratios (FR-009)
- [~] T040 [P] Implement fatal error handling for < 3 valid datasets in Research Mode. **Requirement**: If < 3 valid datasets, exit with code 1 and log exactly: `{"level": "FATAL", "msg": "No sufficient ITS datasets found: <count> valid datasets, minimum required"}` (Edge Cases).
- [~] T041 [P] Add null result handling: generate report explicitly stating "No significant abiotic drivers detected" if p > 0.05
- [ ] T042 [P] Documentation updates in `docs/` and `README.md`
- [ ] T043 Run quickstart.md validation

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must produce real data results before US2/US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US1's data ingestion and cleaning logic.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on US1's PERMANOVA results to sweep thresholds.

### Within Each User Story

- Tests (if included) MUST be **written** and **verified to fail** before implementation
- Data ingestion/cleaning (T013a-T013d) MUST precede statistical analysis (T017-T019)
- Statistical analysis MUST precede reporting (T020-T022)
- Core implementation before integration
- **Memory Safety**: T014b (Projection) MUST run before T015 (MICE) and T016 (VIF).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (as write tasks)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all test WRITING for User Story 1 together (if tests requested):
Task: "Write contract test for ASV table schema validation in tests/contract/test_asv_schema.py"
Task: "Write contract test for environmental metadata schema in tests/contract/test_metadata_schema.py"
Task: "Write integration test for end-to-end pipeline on synthetic data in tests/integration/test_workflow_us1.py"

# Launch data ingestion and cleaning tasks in parallel:
Task: "Implement src/pipelines/ingest.py to download raw FASTQs..."
Task: "Implement MICE imputation in src/pipelines/preprocess.py..."
Task: "Implement VIF calculation in src/pipelines/preprocess.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data ingestion, cleaning, PERMANOVA, db-RDA)
4. **STOP and VALIDATE**: Test User Story 1 independently with real data subset. Ensure `results/permanova_summary.csv` is generated.
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Core analysis)
 - Developer B: User Story 2 (Stratification)
 - Developer C: User Story 3 (Sensitivity)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Verify tests fail before implementing** (Write-first approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All data ingestion tasks MUST use real, reachable URLs or package fetchers. No synthetic data for Research Mode results.
- **CRITICAL**: If RAM limits are approached, subsampling MUST occur before analysis to ensure < 7GB usage.
- **CRITICAL**: VIF > 5 MUST trigger variable removal or PCA combination.
- **CRITICAL**: Strata with < 10 samples MUST be skipped, not crashed.
- **CRITICAL**: PERMANOVA must use exact tests or ≥9999 permutations if n < 20.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence