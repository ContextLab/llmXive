# Tasks: Impact of Environmental Factors on Fungal Community Structure in Soil

**Input**: Design documents from `/specs/001-impact-of-environmental-factors/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.,g., US1, US2, US3)
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
- [X] T002 Initialize Python project with `requirements.txt` (pandas, scikit-learn, scipy, skbio, miceforest, pyyaml, dask, matplotlib, seaborn, cutadapt, vsearch)
- [X] T002a [P] Install CLI tools for sequence processing and data fetching: `cutadapt`, `vsearch`, `seqkit`, and `sra-tools` (via `conda install -c biocore sra-tools` or `apt` in `requirements.txt` post-install script) to enable denoising and SRA data retrieval without R.
- [X] T003 [P] Configure linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes memory safety checks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `src/models/schemas.py` with Pydantic models
 - [X] T004a [P] Implement ASV Table schema (sample_id, asv_id, count)
 - [X] T004b [P] Implement Environmental Matrix schema (sample_id, pH, nutrients, etc.)
 - [X] T004c [P] Implement Results schema (R2, p-value, p-value_adj)
- [X] T005 [P] Implement `src/utils/logging.py` and `src/utils/checksums.py`
 - [X] T005a [P] Implement structured JSON logging in `src/utils/logging.py`
 - [ ] T005b [P] Implement SHA256 verification in `src/utils/checksums.py`
- [X] T006 [P] Configure `src/config/constants.yaml` with thresholds (VIF>5, p<0.05, etc.)
- [X] T008 Configure `src/cli/main.py` entry point with argument parsing for `--mode` (validation vs research) and `--stratify-by`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Environmental-Community Association Analysis (Priority: P1) 🎯 MVP

**Goal**: Ingest public ITS data, harmonize metadata, compute diversity, and run PERMANOVA/db-RDA to identify significant abiotic drivers.

**Independent Test**: The workflow executes on a subset of public datasets and outputs `results/permanova_summary.csv` with significant correlations and `results/db_rda_variance.csv`.

### Pre-Implementation: Tests for User Story 1 (MUST WRITE FIRST) ⚠️

> **NOTE**: These tasks are to **WRITE** the test code first (TDD). They cannot be *executed* until the implementation code exists.

- [X] T010 [P] [US1] **Write** contract test for ASV table schema validation in `tests/contract/test_asv_schema.py`. **Assertion**: Assert that loading invalid JSON (missing required fields) raises a `Pydantic ValidationError`.
- [X] T011 [P] [US1] **Write** contract test for environmental metadata schema in `tests/contract/test_metadata_schema.py`. **Assertion**: Assert that loading CSV with missing columns (pH, nutrients) raises a `Pydantic ValidationError`.
- [X] T012 [P] [US1] **Write** integration test for end-to-end pipeline on synthetic data in `tests/integration/test_workflow_us1.py`. **Assertion**: Assert that the pipeline fails (raises exception) if implementation code is missing for the PERMANOVA step.

### Implementation for User Story 1

- [X] T013a1 [US1] Implement verification logic in `src/pipelines/ingest.py` to count distinct valid datasets. **Requirement**: Verify that at least 3 distinct **SRA accession IDs** are found and validated. If count < 3, log a structured warning and proceed only if in Validation Mode; otherwise, abort with FATAL error (T040). **Execution Order**: This task MUST run BEFORE T013a/T013b.
- [X] T013a [US1] Implement robust dataset download logic in `src/pipelines/ingest.py` for **Validation Mode**:
 - Fetch specific **verified real public datasets** (e.,g., `SRR14338333`, `SRR14338334`, `SRR14338335`).
 - **Fetch**: Use `sra-tools` command `fasterq-dump` to retrieve raw FASTQs.
 - **Streaming**: Implement `gzip.open` in chunks to process reads in batches of [deferred] lines. Do NOT load the entire file into memory. Log chunk size and total bytes to `results/streaming_log.json`.
 - **Deliverable**: Save files to `data/raw-seq/<dataset_id>.fastq.gz` and generate SHA256 checksum.
- [X] T013b [US1] Implement robust dataset discovery and download logic in `src/pipelines/ingest.py` for **Research Mode**:
 - Use **NCBI E-utilities API** (`esearch`/`efetch`) to dynamically search for 'fungal soil AND ITS' datasets.
 - **Query Syntax**: `("fungal soil" OR "mybiome") AND (ITS OR "internal transcribed spacer") AND (sra OR fastq)`
 - **Rate Limiting**: Implement a delay between API calls.
 - **Validation**: Verify that at least 3 distinct **SRA accession IDs** are found and validated.
 - **Fetch**: Use `sra-tools` command `fasterq-dump` to retrieve raw FASTQs.
 - **Streaming**: Implement `gzip.open` in chunks to process reads in batches of [deferred] lines. Do NOT load the entire file into memory. Log chunk size and total bytes to `results/streaming_log.json`.
 - **Constraint**: If running in Research Mode and < 3 distinct datasets found, abort with FATAL error.
 - **Deliverable**: Save files to `data/raw-seq/<dataset_id>.fastq.gz` and generate SHA256 checksum.
- [X] T013d [US1] Implement validation logic in `src/pipelines/ingest.py` to exclude datasets missing required columns (pH, nutrients, etc.) and verify checksums against `data/raw-seq/`. Logs a structured JSON warning: `{"level": "WARN", "msg": "Dataset excluded: missing variable <VAR>", "dataset_id": <ID>}`.
- [X] T013e [US1] Implement construction and validation of Environmental Matrix in `src/pipelines/ingest.py`:
 - **Input**: Metadata CSVs from downloaded datasets.
 - **Action**: Merge and clean metadata. Perform **ontology mapping** to standardize biome labels (e.,g., 'Temperate Forest' -> 'Forest') using a local ENVO lookup table for common synonyms.
 - **Output**: `data/metadata/harmonized_matrix.csv`.
 - **Constraint**: Ensure no NaNs in critical columns (pH, nutrients) before proceeding to T015. If missing values exist, T015 will handle imputation. If critical columns are missing entirely, raise a structured error and exclude the dataset.
- [X] T013c [US1] Implement DADA2/QIIME2-like denoising pipeline in `src/pipelines/preprocess.py` using **pure Python tools**:
 - **Primer Trimming**: Use `cutadapt` via `subprocess` to trim primers.
 - **Denoising**: Use `vsearch` via `subprocess` for error model learning and denoising (no R dependency).
 - **Chimera Removal**: Use `vsearch` via `subprocess` for chimera removal and clustering.
 - **Output**: ASV table to `data/qc/asv_table.tsv`.
 - **Execution Order**: T013c1 (Trimming) -> T013c2 (Denoising) -> T013c3 (Merging) -> T013c4 (Output).
 - [X] T013c1 [US1] Implement quality filtering and primer trimming using `cutadapt`.
 - [X] T013c2 [US1] Implement error model learning and denoising using `vsearch`. **Depends on T013c1**.
 - [X] T013c3 [US1] Implement read merging and chimera removal using `vsearch`. **Depends on T013c2**.
 - [X] T013c4 [US1] Output ASV table to `data/qc/asv_table.tsv`. **Depends on T013c3**.
- [X] T014 [US1] Implement Memory Safety & Streaming Logic in `src/pipelines/ingest.py` and `src/pipelines/preprocess.py`:
 1. Extract `sample_count` and `read_depth` from FASTQ headers using `zcat file.fastq.gz | head -n 4` (or equivalent) for a quick, low-memory check. **Depends on T013a/T013b** (requires actual FASTQ files).
 2. Calculate estimated RAM: `estimated_ram_gb = (sample_count * read_depth * 4.0 bytes_per_read * 1.5 overhead) / 1e9`.
 3. If `estimated_ram_gb > 6.0`, trigger **random subsampling of samples** (FR-009) to ensure peak RAM never exceeds 6GB. **Streaming is a secondary optimization; random subsampling is the mandatory fallback.**
 4. **Runtime Monitoring**: During the denoising process (T013c), monitor actual RAM usage. If actual usage exceeds a predefined threshold, immediately trigger subsampling of the current chunk and log the event.
 5. Log the chunking/subsampling ratio to `results/sampling_report.csv` with columns: `original_n`, `subsampled_n`, `ratio`, `timestamp`.
 6. **Note**: This combines static estimation with runtime monitoring to ensure the hard 7GB constraint is never breached.
- [X] T015 [US1] Implement MICE imputation in `src/pipelines/preprocess.py` using `miceforest` with a configured iteration limit (max 50).
 - **Logic**: Check convergence flag. If `False` after 50 iterations, **exclude samples with missing values** from the dataset.
 - **Verification**: Ensure the remaining dataset has no NaNs before proceeding to VIF calculation (T016). Log excluded samples to `results/excluded_samples.csv`.
 - **Fallback**: If MICE fails, do NOT use global median imputation; strictly exclude the affected samples.
 - **Depends on**: T013e (Environmental Matrix), T014 (Memory Safety).
- [X] T016 [US1] Implement VIF calculation in `src/pipelines/preprocess.py`; remove or PCA-combine variables with VIF > 5 (FR-007, Edge Cases) and depends on the imputed data from T015.
 - **Depends on**: T015.
- [X] T017 [US1] Implement beta-diversity (Bray-Curtis) and alpha-diversity (Shannon, Observed ASVs) calculation in `src/pipelines/preprocess.py` using `skbio`; **Output**: Bray-Curtis distance matrix, Euclidean distance matrix (FR-002), and **`results/alpha_diversity.csv`** containing Shannon and Observed ASV metrics.
 - **Depends on**: T016.
- [X] T018 [US1] Implement PERMANOVA (using `skbio.stats.ordination.permanova`) with ≥999 permutations and Benjamini-Hochberg FDR correction in `src/pipelines/analysis.py`.
 - **Conditional Logic**: If sample size < 20, use `permutations=9999` to approximate exact test.
 - **Input**: Distance matrices from T017; **Output**: `results/permanova_summary.csv` with columns: term, R², p-value, p-value_adj.
 - **Note**: This task uses the Python equivalent of `adonis2` (which is `skbio.stats.ordination.permanova`), not the R function.
 - **Depends on**: T017.
- [X] T019 [US1] Implement variance partitioning (varpart) to quantify unique/shared variance by predictor in `src/pipelines/analysis.py` (FR-004).
 - **Depends on**: T018.
- [X] T020 [US1] Implement db-RDA triplot generation in `src/pipelines/report.py` showing sample clustering by dominant vector. **Output**: `results/plots/db_rda_triplot.png`.
 - **Depends on**: T019.
- [X] T022 [US1] Generate `results/permanova_summary.csv` and `results/db_rda_variance.csv` with FDR-corrected p-values.
 - **Depends on**: T018.
- [X] T046 [US1] Implement **explicit sample size justification** in `results/power_analysis_report.md`. **Requirement**: Calculate and report the minimum detectable effect size (R²) for the given sample count (N) and permutation count (999/9999) at α=0.05 power=0.80 using `statsmodels` power analysis. If power < 0.80, **flag as "Low Power"** in the report but **DO NOT exclude** the study from global meta-analysis (per Spec Edge Cases). **Output columns**: `sample_size`, `permutations`, `alpha`, `power`, `min_effect_size`, `status`.
- [X] T047 [US1] Add **homogeneity of dispersion check** in `src/pipelines/analysis.py` before PERMANOVA. **Requirement**: Run `skbio.stats.distance.betadisper` to test for differences in multivariate dispersion between groups. If significant (p < 0.05), add a warning to `results/permanova_summary.csv` in the format: `{"warning": "Dispersion differs (p < 0.05); PERMANOVA may reflect dispersion rather than location"}`.
- [X] T048 [US1] Implement **collinearity matrix visualization** in `src/pipelines/report.py`. **Output**: `results/plots/correlation_matrix.png`. **Requirement**: Use `seaborn.heatmap` to plot pairwise correlations of environmental variables. Highlight cells where VIF > 5 with a red border.
- [X] T049 [US1] Add **detailed provenance logging** for every data transformation step in `src/utils/logging.py`. **Requirement**: Log the exact command line arguments, software versions, and input file checksums for every step (download, trimming, denoising, merging) to `results/provenance_log.json`. **JSON Schema**: `{"command": "<string>", "args": "<string>", "version": "<string>", "input_checksum": "<string>", "output_checksum": "<string>"}`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Biome-Specific Driver Ranking (Priority: P2)

**Goal**: Stratify analysis by biome/soil type and re-run tests to identify context-specific driver rankings.

**Independent Test**: The workflow runs with `--stratify-by=biome` and generates separate summary tables and plots for each biome.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Contract test for biome-stratified results schema in `tests/contract/test_biome_results_schema.py`
- [X] T024 [P] [US2] Integration test for skipping strata with < 10 samples in `tests/integration/test_stratification.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement stratification logic in `src/pipelines/analysis.py` to split cleaned data by `biome` column (using output from T013e).
- [X] T026 [US2] Implement power check in `src/pipelines/analysis.py`: If stratum sample count < 10, **SKIP** execution of PERMANOVA/varpart for that stratum.
 - **Logging**: Log error to `results/skipped_strata.json` in **structured JSON format**: `{"level": "WARN", "msg": "Stratum skipped: insufficient samples", "biome": "<name>", "count": <n>}`.
 - **Format**: Must match the Edge Cases JSON schema for warnings.
- [X] T027 [US2] Re-run PERMANOVA and varpart for each valid stratum in `src/pipelines/analysis.py`.
- [X] T028 [US2] Generate `results/db_rda_biome_<NAME>.csv` for each biome with R² values.
- [X] T029 [US2] Implement logic to determine top driver per biome. **Input**: Read `results/db_rda_biome_*.csv` files.
 - **Metric**: Sort R² values from each file to derive a rank index for each predictor.
 - **Tie Handling**: If R² values are tied, assign the **average rank** (fractional, e.,g., 1.5). **Use this fractional rank directly in the standard deviation calculation (do NOT round).**
 - **Missing Data**: **Exclude** biomes where the top driver is missing (e.,g., due to non-significance or low sample size) from the SD calculation.
 - **Calculation**: Calculate standard deviation of the rank index of the top driver across **valid** biomes using `numpy.std` or equivalent.
 - **Pass Condition**: Verify standard deviation ≤ 0.5 (SC-003).
 - **Deliverable**: Log the calculated standard deviation and a Pass/Fail flag to `results/biome_ranking_summary.csv`.
 - **Dependency**: This task depends on the **completion** of the loop in T027/T028, ensuring all biome CSVs are generated before aggregation.
- [X] T030 [US2] Generate summary report indicating if top predictor changes across biomes (e.,g., pH in forests, moisture in grasslands).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity and Robustness Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on p-value and R² thresholds to assess the stability of the dominant driver ranking.

**Independent Test**: The workflow runs with `--sweep-thresholds` and outputs `results/sensitivity_analysis.csv` showing driver stability.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Contract test for sensitivity analysis schema in `tests/contract/test_sensitivity_schema.py`
- [X] T032 [P] [US3] Unit test for robustness flagging logic in `tests/unit/test_robustness.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement threshold sweep logic in `src/pipelines/report.py` to iterate p-values across conventional significance thresholds and R² cutoffs across a range of explanatory power benchmarks.
- [X] T034 [US3] Re-evaluate top driver ranking for each threshold combination.
- [X] T035 [US3] Generate `results/sensitivity_analysis.csv` documenting top driver per threshold set.
- [X] T036 [US3] Implement robustness metric calculation: Count rows in `sensitivity_analysis.csv` where top_driver is stable; calculate percentage against total rows; flag Pass if ≥ 80%, Fail otherwise (SC-004).
- [X] T037 [US3] Generate `results/robustness_summary.md` stating the percentage and Pass/Fail status against the 80% threshold.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Generate `results/sampling_report.csv` documenting subsampling ratios (FR-009)
- [X] T040 [P] Implement fatal error handling for < 3 valid datasets in Research Mode. **Requirement**: If < 3 valid datasets, exit with code 1 and log exactly: `{"level": "FATAL", "msg": "No sufficient ITS datasets found: <count> valid datasets, minimum required"}` (Edge Cases).
- [X] T041 [P] Add null result handling: generate report explicitly stating "No significant abiotic drivers detected" if p > 0.05
- [X] T042 [P] Documentation updates in `docs/` and `README.md`
- [X] T043 Run quickstart.md validation
- [X] T044 Reconcile run-book vs implementation for `code/utils/checksums.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/checksums.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

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
- Data ingestion/cleaning (T013a-T013e) MUST precede statistical analysis (T017-T019)
- Statistical analysis MUST precede reporting (T020-T022)
- Core implementation before integration
- **Memory Safety**: T014 (Streaming/Projection) MUST run after T013 (Ingestion) and before T015 (MICE) and T016 (VIF).
- **Dataset Verification**: T013a1 MUST run before T013a/T013b.
- **Environmental Matrix**: T013e MUST run before T015 (MICE) and T016 (VIF).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (as write tasks)
- Different user stories can be worked on in parallel by different team members

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
- **CRITICAL**: If RAM limits are approached, **random subsampling** MUST occur (FR-009). Streaming is secondary.
- **CRITICAL**: VIF > 5 MUST trigger variable removal or PCA combination.
- **CRITICAL**: Strata with < 10 samples MUST be skipped, not crashed.
- **CRITICAL**: PERMANOVA must use exact tests or ≥9999 permutations if n < 20.
- **CRITICAL**: MICE failure MUST trigger sample exclusion, not median imputation.
- **CRITICAL**: All logs must follow the structured JSON schema defined in Edge Cases.
- **CRITICAL**: Task T040 must use the exact message: "No sufficient ITS datasets found: <count> valid datasets, minimum required".
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T044 Reconcile run-book vs implementation for `code/utils/checksums.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/checksums.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
