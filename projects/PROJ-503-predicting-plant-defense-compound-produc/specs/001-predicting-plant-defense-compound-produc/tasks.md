# Tasks: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Input**: Design documents from `/specs/001-predicting-plant-defense/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: User story tests are REQUIRED per spec.md Independent Test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Full repo paths**: All paths MUST use full repository path: `projects/PROJ-503-predicting-plant-defense-compound-produc/`
- **Never use relative paths**: Do NOT use `code/`, `tests/`, `logs/` without the full repo prefix
- **Example**: `projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`

<!--
 ============================================================================
 IMPORTANT: The tasks below are generated based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment
 ============================================================================
-->

## Phase 0: Data Discovery, Acquisition & Foundation (MANDATORY BLOCKER)

**Purpose**: Verify dataset availability, download specific verified datasets, and enforce strict pairing abort. **All foundational infrastructure (Structure, Checksum, Data Models, Errors, Logging) MUST be in place BEFORE data acquisition.**

**⚠️ ABORT CRITERIA**: If no verified plant omics datasets are found or pairing < 95%, project halts with E-DATASET or E-PAIRING.

### Phase 0.0: Project Structure & Foundation (Must run BEFORE T001)

- [X] T014a [P] [Plan-T014] **Create script**: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/scripts/setup_dirs.sh` containing the exact `mkdir -p` command for all required directories. **Must be the first task in Phase 0.0.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/scripts/setup_dirs.sh`)

- [X] T014b [P] [Plan-T014] **Execute script**: Run `scripts/setup_dirs.sh` to create all directories. **Output: All directories must exist.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/scripts/run_setup.sh`)

- [X] T014c [P] [Plan-T014] **Verify directories**: Create unit test `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_directories.py` to verify existence of all required directories. (`projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_directories.py`)

- [X] T022 [P] [Plan-T022] Create SHA-256 checksum validation utility for data integrity (SC-004). **Acceptance: Utility function `validate_checksum(file_path, expected_hash)` validates file checksums against a provided manifest.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/checksum.py`)

- [X] T019a [P] [Plan-T019] **Implement ExpressionMatrix**: Create class `ExpressionMatrix` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`. **Define attributes: Rows=genes, Columns=samples, values=TPM. Include `__init__`, `to_csv`, `from_csv` methods. Data types: numpy.float64 for values, str for IDs. Validation: ensure columns are numeric and rows are unique. `to_csv` method: delimiter=',', NA handling: empty string, column order: gene_id, sample_1,...** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`)

- [X] T019b [P] [Plan-T019] **Implement MetaboliteMatrix**: Create class `MetaboliteMatrix` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`. **Define attributes: Rows=metabolites, Columns=samples, values=log-conc. Include `__init__`, `to_csv`, `from_csv` methods. Data types: numpy.float64 for values, str for IDs. Validation: ensure columns are numeric and rows are unique.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`)

- [X] T019c [P] [Plan-T019] **Implement FeatureSet**: Create class `FeatureSet` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`. **Define attributes: Subset of genes from ExpressionMatrix. Include `__init__`, `to_csv`, `from_csv` methods.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`)

- [X] T019d [P] [Plan-T019] **Implement ModelArtifact**: Create class `ModelArtifact` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`. **Define attributes: Serialized Ridge Regression coefficients and evaluation metrics. Include `__init__`, `to_json`, `from_json` methods.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/data_models.py`)

- [X] T020-FRAMEWORK [P] [Plan-T020] Setup environment configuration management and error handling framework structure. **Create `projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/config.py` for config, and `projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/errors.py` with base Exception class. Define config schema in `docs/config_schema.yaml` and implement `config.py` to load it.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/config.py`)

- [X] T020-ERR [P] [Plan-T020] Implement specific error classes: `E-DATASET`, `E-PAIRING`, `E-TIMEOUT`, `E-POWER`. **Acceptance: Exception classes defined (e.g., `class E_PAIRING(Exception)`) and raised correctly in unit tests. Must enforce FR-008 abort logic.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/errors.py`)

- [X] T017 [P] [Plan-T017] Implement logging logic: Create utility functions to write to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` (on mismatch) and `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` (edge case handling). **Acceptance: Logs must be JSON/CSV valid and contain required fields. Function signature: `log_mismatch(sample_id, reason)` and `log_filter(gene_id, variance)`.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/logging.py`)

- [X] T021a [P] [FR-008] **Create runtime_monitor.json schema**: Create the schema definition for `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/runtime_monitor.json` with fields {elapsed_seconds, cpu_cores, phase_start_time}. **Deliverable: A JSON schema file or documented structure that defines the exact format and data types for the runtime monitor.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/runtime_monitor.py`)

- [X] T021b [P] [FR-008] **Implement timer initialization**: Create function `start_timer()` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/runtime_monitor.py` that initializes `runtime_monitor.json` using the schema from T021a. **Logic: Record start time, set elapsed_seconds to 0, record cpu_cores.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/runtime_monitor.py`)

- [X] T021c [P] [FR-008] **Implement abort check**: Create function `check_time_limit()` in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/runtime_monitor.py` that reads `runtime_monitor.json` and raises `E-TIMEOUT` if >4h. (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/utils/runtime_monitor.py`)

- [X] T021d [P] [FR-008] **Integrate check**: Integrate `check_time_limit()` into main loop and phase boundaries. **Must run before any data acquisition tasks (T001a, T001a-2, T002a).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/main.py`)

- [X] T010 [P] [Plan-T010] Setup environment configuration management: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` for dataset version traceability. **Content: Document each accession, download date, AND the dataset's release version (e.g., GEO release date). If script version is unknown, use [deferred]. No null fields allowed.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml`)

### Phase 0.1: Data Acquisition & Verification

- [X] T000a [US1] [FR-001] **Verify GSE21857**: Verify availability of GSE21857 (*Arabidopsis*). **Abort with E-DATASET if not found or not herbivore-stress.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [X] T000b [US1] [FR-001] **Verify GSE167633**: Verify availability of GSE167633 (*Solanum*). **Abort with E-DATASET if not found or not herbivore-stress.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [X] T000c [US1] [FR-002] **Verify ST002565**: Verify availability of ST002565 (Metabolomics Workbench). **Abort with E-DATASET if not found.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [X] T000d [US1] [FR-001] **Aggregate and Abort**: Aggregate results from T000a, T000b, T000c. **If any fail, raise E-DATASET and halt pipeline BEFORE T001a/T001a-2/T002a.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data_download.py`)

- [X] T001a [US1] [FR-001] [SC-004] **Download GSE21857**: Download gene expression matrix from GEO for GSE21857. **Source: GEO FTP/ArrayExpress. Output: Raw zip file `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/geo_GSE21857.zip`. MUST fail loudly if download fails; NO synthetic fallback. Raise E-DATASET on failure.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/download.py`)

- [X] T001a-2 [US1] [FR-001] [SC-004] **Download GSE167633**: Download gene expression matrix from GEO for GSE167633. **Source: GEO FTP/ArrayExpress. Output: Raw zip file `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/geo_GSE167633.zip`. MUST fail loudly if download fails; NO synthetic fallback. Raise E-DATASET on failure.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/download.py`)

- [X] T002a [US1] [FR-002] [SC-004] **Download ST002565**: Download metabolite data from Metabolomics Workbench for ST002565. **API Endpoint: Metabolomics Workbench Study API. Output: Raw data file `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/metabolomics_ST002565.zip`. MUST fail loudly if download fails; NO synthetic fallback. Raise E-DATASET on failure.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/download.py`)

- [X] T003a [US1] [SC-004] **Generate checksum manifest**: Generate `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/checksums.json` from downloaded files (T001a, T001a-2, T002a). **Output: JSON manifest with file paths and SHA-256 hashes.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/verify_checksums.py`)

- [X] T003 [US1] [SC-004] **Verify checksums**: Verify checksums for all downloaded files using `checksums.json` (T003a). **Verify SC-004: "Downloaded files... must match expected checksums (SHA-256) for ≥99% of requested experiment IDs". Implement aggregate check logic. Raise `E-DATASET` if aggregate match rate is <99%. Abort with E-DATASET if <99% match *before any downstream processing*.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/verify_checksums.py`)

- [X] T001b [US1] [FR-001] [SC-004] **Parse GSE21857**: Parse GEO raw zip file into WIDE FORMAT CSV. **Input: Raw zip from T001a. Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/geo_expression_matrix_GSE21857.csv`. Logic: Parse '!Sample_title' and '!Sample_accession' to create WIDE FORMAT {gene_id, sample_1, sample_2,...}. **DEPENDS ON T003 PASS**. Do NOT normalize here.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/parse.py`)

- [X] T001b-2 [US1] [FR-001] [SC-004] **Parse GSE167633**: Parse GEO raw zip file into WIDE FORMAT CSV. **Input: Raw zip from T001a-2. Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/geo_expression_matrix_GSE167633.csv`. Logic: Parse '!Sample_title' and '!Sample_accession' to create WIDE FORMAT {gene_id, sample_1, sample_2,...}. **DEPENDS ON T003 PASS**. Do NOT normalize here.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/parse.py`)

- [X] T002b [US1] [FR-002] [SC-004] **Parse ST002565**: Parse Metabolomics Workbench raw files into WIDE FORMAT CSV. **Input: Raw zip from T002a. Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/metabolite_matrix.csv`. Logic: Map 'Study Accession' to 'sample_id' and 'Compound Name' to 'metabolite_id'. Output: WIDE FORMAT {metabolite_id, sample_1, sample_2,...}. **DEPENDS ON T003 PASS**. Do NOT log-transform here.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/parse.py`)

- [X] T004 [US1] [FR-002] Pair samples by biological sample ID (`biosample_id`). **Input: CSVs from T001b, T001b-2, T002b. Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/paired_index.csv`. Log mismatches to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` (Schema: JSON array with `sample_id`, `reason`).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/pairing.py`)

- [X] T005 [US1] [FR-009] [SC-005] **Abort with E-PAIRING**: Read `paired_index.csv` (T004) to calculate pairing rate. **Abort with E-PAIRING if pairing rate on the *final* paired set is < 95% (FR-009, SC-005).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/pairing.py`)

- [X] T006 [US1] Create `PairedSampleIndex` artifact (list of valid sample IDs) and save to `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/paired_samples.csv`.

- [X] T007 [US1] Perform post-verification check: Ensure *every* sample in `PairedSampleIndex` has both expression and metabolite data. If any mismatch remains, exclude and log. **Deliverable: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/post_pairing_verification.json` with schema {verified_samples, excluded_samples, reason}.**

- [X] T008 [US1] [SC-001] Perform power analysis on the final paired set using `statsmodels.stats.power.tt_solve_power` (F-test, effect size r=0.5, alpha 0.05, power 0.8). **Verify SC-001: "Pearson correlation coefficient (r) between predicted and observed abundance must be ≥ 0.5". **Abort with E-POWER if N < 40** (Minimum Viable N to achieve sufficient power for r=0.5).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/data/power_analysis.py`)

- [X] T009 [US1] Create `research.md` with dataset citations and availability status for Phase 0. **Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/research.md`.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/docs/research.md`)

**Checkpoint**: Phase 0 complete - datasets verified, paired, and power analysis passed OR project aborted. **Phase 1 cannot begin until T008 passes.**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T015 [US1] [Plan-T015] Initialize Python project with requirements.txt at `projects/PROJ-503-predicting-plant-defense-compound-produc/code/requirements.txt` (pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, statsmodels, pytest, pycombat)

- [X] T016 [US1] [Plan-T016] Configure linting and formatting: Create `projects/PROJ-503-predicting-plant-defense-compound-produc/.flake8` and `projects/PROJ-503-predicting-plant-defense-compound-produc/pyproject.toml` with black configuration

- [X] T058a [P] [Constitution-I] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart.md` with E2E pipeline instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end data acquisition & pairing (Priority: P1) 🎯 MVP

**Goal**: Obtain paired dataset of gene‑expression profiles and defense‑metabolite concentrations for Arabidopsis and Solanum samples under herbivore stress

**Independent Test**: Run the data‑download module on specified GEO series IDs and Metabolomics Workbench experiment IDs and verify that every expression sample has a matching metabolite record from the same biological sample.

### Tests for User Story 1 (REQUIRED per spec.md Independent Test) ⚠️
*(Moved to Phase 0 for early validation)*

### Implementation for User Story 1

- [X] T025 [US1] Create expression CSV with normalized TPM/FPKM values for each sample. **Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/expression_matrix.csv`. Schema: WIDE FORMAT {gene_id, sample_1, sample_2,...}. **DEPENDS ON T004, T006, T007**. **Normalize using exact methods defined in FR-003** (TPM/FPKM calculation). Verify: Run `tests/unit/test_matrix_schema.py` against the output file.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T026 [US1] Create metabolite CSV with log‑transformed concentrations aligned by experimental sample identifier (US-1 acceptance scenario 2). **Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/metabolite_matrix.csv`. Schema: WIDE FORMAT {metabolite_id, sample_1, sample_2,...}. **DEPENDS ON T004, T006, T007**. **Log-transform using exact methods defined in FR-003** (log base e or 10 as specified). Verify: Run `tests/unit/test_matrix_schema.py` against the output file.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T027 [US1] Log mismatches to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json` with fields {sample_id, expression_source, metabolite_source, reason: "no_sample_level_pair"} (edge case handling)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature selection & preprocessing (Priority: P2)

**Goal**: Isolate expression features belonging to known defense‑biosynthetic pathways and ensure both expression and metabolite matrices are properly normalized before modelling

**Independent Test**: Execute the feature‑selection module and confirm that the resulting feature matrix contains only genes whose KEGG IDs map to terpenoid, alkaloid, or phenylpropanoid pathways.

### Tests for User Story 2 (REQUIRED per spec.md Independent Test) ⚠️

- [X] T028 [P] [US2] Contract test for KEGG pathway mapping in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_kegg_mapping.py`
- [X] T029 [P] [US2] Integration test for feature selection pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_feature_selection.py`

### Implementation for User Story 2

- [X] T030 [US2] [FR-003] Implement expression normalization to TPM/FPKM in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003). **Input: Raw wide-format from T001b/T001b-2. Output: Normalized matrix.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T031 [US2] [FR-003] Implement metabolite log‑transformation in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003). **Input: Raw wide-format from T002b. Output: Log-transformed matrix.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T032 [US2] [FR-004] **Implement KEGG fetch and mapping pipeline**: Implement a single pipeline step that (1) Fetches KEGG pathway data for terpenoid, alkaloid, and phenylpropanoid pathways from KEGG API and (2) Maps gene IDs to these pathways. **Input: Expression matrix (T025). Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed/kegg_mapping.json` (Schema: JSON array with gene_id, kegg_id, pathway_id, confidence_score). LOGIC: Fetch data first; if Fetch fails, raise E-DATASET immediately and abort. Only if Fetch succeeds, proceed to Map step. Log unmapped genes.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T054 [US2] [FR-004] Implement VIF collinearity diagnostics and create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/vif_diagnostics.csv` with columns gene_id, vif_score, threshold_exceeded. **Calculation: `statsmodels.stats.outliers_influence.variance_inflation_factor`. Action: Log warning if VIF > 5.0, do not drop features (Ridge handles collinearity). **DEPENDS ON T032**.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T033 [US2] Create FeatureSet output matrix containing only pathway-mapped genes (US-2 acceptance scenario 1). **DEPENDS ON T054.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T034 [US2] [FR-003] Implement zero‑variance gene filtering (variance < 1e-10) in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-003). **Input: FeatureSet (T033).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T035 [US2] Log zero-variance genes to `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/feature_filtering.csv` with columns gene_id, variance, reason: "zero_variance". **Use log_filter(gene_id, variance) from T017. Append a summary row with the total count of removed genes.** (edge case handling)

- [X] T036 [US2] [FR-010] Implement species-specific z-score normalization in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py` (FR-010). **Input: FeatureSet (T033).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T037 [US2] [FR-010] Implement ComBat batch correction for cross-species expression scale differences (FR-010). **Input: Data after T036 (z-score).** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/preprocessing.py`)

- [X] T038 [US2] Implement ortholog fallback for unannotated *Solanum* genes using *Arabidopsis* reference. **Threshold: Default 60% sequence identity (unless overridden by T010). Log substitutions.** (edge case handling)

- [X] T039 [US2] Document ortholog substitutions in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/edge_cases.md` with original gene ID, substituted gene ID, and sequence identity percentage

- [X] T040 [US2] Verify ≥75% of known defense pathway genes retained per species (SC-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive modelling & evaluation (Priority: P3)

**Goal**: Train a Ridge Regression model to predict defense‑metabolite abundance from the selected gene-expression features and assess performance using cross-validation and permutation testing

**Independent Test**: Run the modelling script on the paired dataset and verify that it reports RMSE, Pearson r, and a permutation-test p-value for each metabolite.

### Tests for User Story 3 (REQUIRED per spec.md Independent Test) ⚠️

- [X] T041 [P] [US3] Contract test for Ridge Regression model training in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_ridge_model.py`
- [X] T042 [P] [US3] Contract test for permutation testing in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract/test_permutation_test.py`
- [X] T043 [P] [US3] Integration test for end-to-end modeling pipeline in `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [X] T044 [US3] [FR-005] Implement outer k-fold cross-validation split with constraint of maintaining paired samples (Plan T031). **Output: Fold indices.**

- [X] T045a [US3] [FR-005] **Implement nested CV split logic**: Create logic to generate outer and inner fold indices from paired samples. **Input: Paired samples (T006). Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/fold_indices.csv`. Logic: Cross-validation, stratified by species if possible. Separates outer and inner splits.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py`)

- [X] T045b [US3] [FR-005] **Implement inner CV alpha tuning loop**: Execute the inner loop to tune alpha. **Input: Fold indices (T045a), Feature matrix. Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/alpha_values.csv`. Logic: Inner k-fold CV, search log-spaced alpha values, metric: neg_mean_squared_error. This task performs ONLY the tuning, not the final training.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py`)

- [X] T045c [US3] [FR-005] **Train final model**: Train the final Ridge Regression models using the tuned alpha. **Input: Fold indices (T045a), alpha values (T045b), Feature matrix. Output: Model objects for each outer fold. Logic: Train Ridge on outer training sets using best alpha from T045b.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py`)

- [X] T045d [US3] [FR-005] **Serialize model** artifacts. **Input: Trained models (T045c). Output: `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/ridge_species_A_model.pkl`, `ridge_species_S_model.pkl`. Logic: Save coefficients and metrics.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py`)

- [X] T046 [US3] [SC-001] Report mean RMSE and Pearson r across outer folds for each metabolite (SC-001).

- [X] T047 [US3] [FR-006] Implement max-T permutation test with 1 000 iterations in `projects/PROJ-503-predicting-plant-defense-compound-produc/code/evaluation.py` (FR-006). **Output: `outputs/metrics/permutation_pvalues.csv`. n_iter=1000. random_state. Method: Max statistic across metabolites per permutation. **Perform test for EACH METABOLITE** and report p-values per metabolite.** **Depends on T045c.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/evaluation.py`)

- [X] T048 [US3] [FR-006] Report two‑sided p‑value ≤ 0.05 for metabolites showing true predictive signal (US-3 acceptance scenario 2) (FR-006).

- [X] T049 [US3] [FR-007] Apply Bonferroni correction across all metabolites tested (FR-007).

- [X] T050 [US3] [SC-001] Verify Pearson r ≥ 0.5 for metabolite with highest correlation across 5‑fold CV (SC-001)

- [X] T051 [US3] [SC-002] Verify the **Bonferroni-corrected p-value** for the metabolite with the highest Pearson r is ≤ 0.05 (SC-002).

- [X] T052 [US3] [FR-008] Log runtime and resource usage; abort if CPU time exceeds a predefined computational budget (FR-008).

- [X] T053 [US3] Serialize ModelArtifact (coefficients and evaluation metrics) to `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/`

- [X] T055 [US3] [FR-010] Train cross-species model (FR-010): Create `projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models/cross_species_ridge.pkl`. **Input: Data after T036/T037 (z-score + ComBat). Model: Single Ridge instance trained on combined, batch-corrected data.** (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/modeling.py`)

- [X] T056 [US3] Validate species-holdout generalization (train on A, test on S; train on S, test on A). **Implement `validate_holdout.py` which trains on A/test on S and vice versa, saves results to `outputs/metrics/species_holdout_results.csv`, and raises an error if the model fails the threshold.** If holdout fails, discard cross-species model. **Output: `outputs/metrics/species_holdout_results.csv`.**

- [X] T057 [US3] Validate that predictions are not driven by species identity (e.g., train a null model with only species as a predictor)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T058b [P] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/data-model.md` with schema definitions for ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact
- [X] T058c [P] Create `projects/PROJ-503-predicting-plant-defense-compound-produc/contracts/` directory with module specifications

- [X] T059a [P] Run linting and formatting: Execute `black --check` and `flake8`; fix all violations.
- [X] T059b [P] Update `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/refactoring_log.md` with changes made.

- [X] T060a [P] Profile pipeline: Run `cProfile`; identify bottlenecks. **Generate `logs/profile_output.prof`.**

- [X] T060b-1 [P] **Identify bottleneck**: Analyze `logs/profile_output.prof` (T060a) to identify the top 3 bottlenecks. (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/optimization.py`)

- [X] T060b-2 [P] **Implement specific optimization**: Implement specific optimization for identified bottlenecks (e.g., vectorize matrix operations in preprocessing). (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/optimization.py`)

- [X] T060b-3 [P] **Verify performance improvement**: Re-run `cProfile` and verify runtime reduction or memory improvement. (`projects/PROJ-503-predicting-plant-defense-compound-produc/code/optimization.py`)

- [X] T060c [P] Verify E2E runtime: Run `tests/integration/test_e2e_runtime.py` to verify E2E runtime <4h (SC-003).

- [X] T061 [P] Create unit tests with ≥80% line coverage: `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_data_download.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_preprocessing.py`, `projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit/test_modeling.py`

- [X] T062 [P] Run quickstart.md validation: Execute quickstart.md instructions on fresh environment; verify all steps complete without error; document in `projects/PROJ-503-predicting-plant-defense-compound-produc/docs/quickstart_validation.md`

- [X] T063 [P] Commit all artifacts; tag release with content hash version.
- [X] T064 [US3] Generate final consolidated report with all metrics, logs, and artifacts.