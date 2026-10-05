---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-degradation/`
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

## Phase 1: Setup & Amendments (Shared Infrastructure + Blocking Prerequisites)

**Purpose**: Project initialization, spec/constitution amendment proposals, and basic structure.
**Note**: ALL SPEC AND CONSTITUTION AMENDMENT PROPOSALS MUST BE GENERATED HERE. Ratification occurs in Phase 2.

- [ ] T001a Create project directory structure: Execute `mkdir -p code/ data/raw/ data/processed/ data/reports/ tests/ state/ state/projects/` in repository root. **Verification**: Verify directories exist via `test -d code/ && test -d data/raw/` and `tree data/` output. (Constitution I)
- [ ] T001b (Depends on T001a) Verify project directory structure: Run `test -d code/ && test -d data/raw/ && test -d data/processed/` and `tree data/` to confirm all directories exist. (Constitution I)
- [ ] T002a Generate `code/requirements.txt` with pinned versions: `rdkit==2023.9.5`, `torch==2.1.0`, `torch-geometric==2.4.0`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `pyyaml==6.0.1`, `requests==2.31.0`, `statsmodels==0.14.0`, `pytest==7.4.3`. **Note**: Use `--extra-index-url https://download.pytorch.org/whl/cpu` when installing torch to ensure CPU wheels are used.
- [ ] T002b (Depends on T002a) Verify installation: Run `pip check` and `python -c "import torch; print(torch.__version__)"` to confirm installation.
- [ ] T003a Configure linting tool `ruff` in `code/.ruff.toml` with strict rules for reproducibility and type checking.
- [ ] T003b (Depends on T003a) Verify ruff configuration: Run `ruff check code/` and verify exit code 0.
- [ ] T004a (Depends on T001a) Setup shared logging infrastructure with file handlers in `code/utils.py`. **Verification**: Run `python -c "from utils import setup_logger; print('OK')"`.
- [ ] T004b (Depends on T004a) Verify logging setup: Run `python -c "from utils import get_logger; print('OK')"`.
- [ ] T005 (Depends on T001a) Implement exponential backoff utility (with a configurable retry limit) in `code/utils.py` for API rate limiting. **Verification**: Run `python -c "from utils import exponential_backoff; print('OK')"`.
- [ ] T006 (Depends on T001a) Create base configuration loader for environment variables and paths in `code/utils.py`. **Verification**: Run `python -c "from utils import load_config; print('OK')"`.
- [ ] T007a (Depends on T001a) Define `PolymerRecord` data class in `code/data_models.py`: Fields `smiles`, `temperature`, `ph`, `uv`, `degradation_pathway`, `source_id`. (FR-001, FR-008)
- [ ] T007b (Depends on T001a) Define `MolecularGraph` data class in `code/data_models.py`: Fields `atom_features`, `bond_features`, `edge_index`, `environment_vector`. (FR-002)
- [ ] T007c (Depends on T001a) Define `MotifImportance` data class in `code/data_models.py`: Fields `motif_pattern`, `pathway`, `importance_score`, `p_value`. (FR-007, SC-002)
- [ ] T008a (Depends on T001a) Create `pytest.ini` with seed pinning and `conftest.py` for shared fixtures in `tests/`. **Verification**: Run `pytest --collect-only` and verify exit code 0.
- [ ] T008b (Depends on T008a) Implement seed pinning fixture in `tests/conftest.py`: `pytest.fixture(autouse=True) def set_seed(): random.seed(a_fixed_value); np.random.seed()`. **Verification**: Run `pytest tests/unit/test_seed.py` and verify reproducibility.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites + Ratification)

**Purpose**: Core infrastructure, data models, and **ratification** of amendment proposals from Phase 1.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Amendment proposals must be ratified here before dependent tasks start.

- [ ] T017c (Depends on T007a) **RATIFY AMENDMENT**: Ratify the proposal to use `statsmodels` instead of G*Power for power analysis (SC-004).
  - **Logic**: Verify the citation for `statsmodels.stats.power.tt_ind_solve_power` against the primary source (statsmodels documentation or paper). Update `state/amendment_log.yaml` with the ratified status.
  - **Verification**: Verify `state/amendment_log.yaml` contains the ratified amendment ID and status "ratified". (Constitution II, Plan Correction)

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output parquet contains valid SMILES strings, numeric environmental parameters, and categorical degradation labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Unit test for SMILES validation and RDKit graph conversion in `tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid`
- [ ] T010 [US1] Unit test for missing data exclusion logic in `tests/unit/test_preprocess.py::test_missing_env_excludes_record`
- [ ] T012 [US1] Integration test for API rate-limit backoff in `tests/integration/test_api_ingestion.py::test_backoff_on_rate_limit`

### Implementation for User Story 1

- [ ] T013 [US1] (Depends on T005, T006) Implement `ingest.py`: Download records from NIST (URL: `https://webbook.nist.gov/cgi/cbook.cgi?ID=...`) and Materials Project (API Endpoint: `https://materialsproject.org/rest/v/materials/...`) with rate-limit backoff.
  - **Primary Logic**: Attempt to fetch real records. If APIs return no data or rate-limit after 3 retries, **FAIL** and log "API_FAILURE". Do NOT generate synthetic data here.
  - **Output**: Save to `data/raw/raw_nist_mp_records.csv` with schema: `[smiles, temperature, ph, uv, source_id]`. If download fails, the script must exit with error code 1. (FR-001, FR-008, Constitution I)
- [ ] T013b [US1] (Depends on T013) **SYNTHETIC STRUCTURE Fallback Generator**: If T013 fails, generate a synthetic *structure* dataset.
  - **Logic**: Run `python code/generate_synthetic_structure.py --seed 42`.
  - **Synthetic Logic**: Generate a `data/raw/synthetic_seed.json` file with schema: `{"smiles": [string], "temperature": [float], "ph": [float], "uv": [float], "source_id": [string]}`. **DO NOT** assign `degradation_pathway` here.
  - **Output**: Save to `data/raw/raw_nist_mp_records.csv` (overwriting or merging) with synthetic structure data. Log "SYNTHETIC_STRUCTURE_GENERATED". (FR-001, FR-008)
- [ ] T014 [US1] (Depends on T013, T013b) Implement `ingest.py`: Identify records missing 'degradation pathway' labels and apply synthetic labels or flag for curation.
  - **Logic**: Scan ingested data for missing `degradation_pathway`.
  - **Halt Condition**: If `N=0` (no records), raise `FatalError("HALT: No records found")` and log to `data/raw/halt_log.txt`.
  - **Apply Logic**: If `N>0` and all records are missing labels:
    - If `CONFIG_ALLOW_SYNTHETIC` is true (default): Apply synthetic labels with a distribution emphasizing hydrolysis, alongside oxidation and photolysis. Log "SYNTHETIC_LABELS_APPLIED".
    - If `CONFIG_ALLOW_SYNTHETIC` is false: Raise `FatalError("HALT: All records missing labels and synthetic fallback disabled")` and log to `data/raw/halt_log.txt`.
  - **Partial Missing**: If SOME records are missing labels, apply synthetic labels to the missing ones and flag them in `data/raw/flagged_for_curation.csv`.
  - **Output**: Save to `data/raw/raw_polymer_records.csv` with synthetic labels applied (if applicable). (FR-001, FR-008, US-1 Scenario 4)
- [ ] T015 [US1] (Depends on T014) Implement `preprocess.py`: Convert SMILES to molecular graphs using RDKit (parameters: `sanitize=True`, `removeHs=False`); filter non-polyesters by detecting ester functional groups (SMARTS pattern: `C(=O)O`) in SMILES.
  - **Handling Missing Environmental Data**: For records missing environmental data (temp/pH/UV), the system MUST: 1) FLAG the record in `data/raw/flagged_env_missing.csv`, and 2) APPLY documented defaults (pH 7.0, 25°C, 0 UV) as per FR-002. The record is then INCLUDED in the training set with the imputed values. The log MUST explicitly record the imputation action. (FR-002, US-1 Scenario 2)
  - **Output**: Save to `data/processed/graphs.parquet` (FR-002)
  - **Error Handling**: If RDKit conversion fails for a SMILES string, skip the record, log the SMILES, and continue.
  - **Output**: Generate `data/processed/exclusion_decision_log.json` with schema `{excluded_count: int, excluded_smiles: [string]}` confirming the exclusion path was taken and documenting the count of excluded records. (FR-002, Plan: Data Exclusion Assumption, Methodological Correction)
- [ ] T016 [US1] (Depends on T013, T015) **ARTIFACT SAVE**: Save the raw ingested dataset (T013) and processed graph dataset (T015) with checksums.
  - **Logic**: Save raw data to `data/raw/raw_polymer_records.csv` (post-labeling) and processed data to `data/processed/processed_graph_dataset.parquet`.
  - **Command**: `python code/utils.py --checksum sha256 --input data/raw/raw_polymer_records.csv --output state/artifact_hashes.yaml`.
  - **Verification**: Verify checksums and file existence. (FR-001, FR-002)
- [ ] T016b [US1] (Depends on T016) **PRE-AUGMENTATION SAVE**: Save the pre-augmentation dataset (after environmental imputation but before augmentation) to `data/processed/pre_augmented_graph_dataset.parquet` with checksums. This artifact is the input for the augmentation phase in Phase 4. (FR-002)
- [ ] T017a [US1] (Depends on T016b, T017c) **POWER ANALYSIS LOGIC**: Implement the power analysis logic in `code/preprocess.py` (function `calculate_power_analysis`).
  - **Amendment Reference**: Uses `statsmodels.stats.power.tt_ind_solve_power` (Ratified in T017c).
  - **Logic**: Calculate sample size `n` from the *pre-augmentation* dataset. If `n > 150`, subsample to 150 using stratified sampling (seed 42). If `n <= 150`, determine action: "augment" (50<=n<150) or "augment_aggressive" (n<50).
  - **Output**: Return `{"n": int, "action": "none" | "augment" | "augment_aggressive"}`. (SC-004, FR-004, Plan Correction)
- [ ] T017b [US1] (Depends on T017a) **POWER ANALYSIS EXECUTION**: Execute `python code/preprocess.py --mode power_analysis`.
  - **Logic**: Call the implemented logic. Write `state/augmentation_trigger.json` with `{"n": int, "action": "none" | "augment" | "augment_aggressive"}`. Generate `data/reports/power_analysis_warning.json` with `{"n": int, "warning": "true" if n<150 else "false"}`.
  - **Verification**: Verify `state/augmentation_trigger.json` exists and contains valid keys `n` and `action`. (SC-004, FR-004, Plan Correction)
- [ ] T025 [US1] (Depends on T017b, T016b) **DATA AUGMENTATION**: Apply data augmentation via **edge dropout** and **subgraph sampling** as mandated by FR-004.
  - **Logic**: Read `state/augmentation_trigger.json`. If action is "none", skip. If "augment" or "augment_aggressive", proceed.
  - **Command**: `python code/augment.py --input data/processed/pre_augmented_graph_dataset.parquet --output data/processed/augmented_graph_dataset.parquet --method edge_dropout,subgraph_sampling --seed 42`.
  - **Algorithm**:
    1. Use PyTorch Geometric `RandomLinkDrop` with probability=0.2 for edge dropout.
    2. Apply subgraph sampling with `node_ratio=0.8`.
    3. Generate new graph objects with the modified features.
  - **Rationale**: Edge dropout and subgraph sampling are required by FR-004 to expand the dataset while preserving topology.
  - **Validation**: Verify that the augmented dataset size is **substantially larger** than the pre-augmentation size.
  - **Verification**: 
    1. Verify `data/processed/augmented_graph_dataset.parquet` row count == 2 * `data/processed/pre_augmented_graph_dataset.parquet` row count.
    2. Verify `data/processed/augmentation_log.json` contains `{"edge_dropout": true, "subgraph_sampling": true}`.
    3. Fail immediately if not equal or if flags are missing.
  - **Output**: Save the augmented dataset to `data/processed/augmented_graph_dataset.parquet`. (FR-004, Plan Phase 2)
- [ ] T025b [US1] (Depends on T025) **AUGMENTATION VALIDATION & SAVE**: Validate chemical integrity of the augmented dataset.
  - **Output**: Save the final dataset to `data/processed/final_dataset.parquet` with checksums.
  - Measure runtime and log to `data/reports/augmentation_timing.json`. **Constraint**: Read `max_duration_minutes` from `code/config.yaml`. If duration > `max_duration_minutes`, log a FAIL status; otherwise PASS.
  - Log the action to `data/processed/augmentation_log.json`. (FR-004, US-2 Scenario 3)
- [ ] T019 [US1] (Depends on T025b) **DATA INTEGRITY CHECK**: Verify the checksums of the final dataset artifact. Log any discrepancies. (Plan: Data Hygiene)
- [ ] T019b [US1] (Depends on T025b) **METADATA GENERATION**: Generate `data/processed/dataset_metadata.json` containing the count of records, count of excluded records, and the action taken (none/augment/augment_aggressive). (Plan: Data Hygiene)
- [ ] T020 [US1] (Depends on T007a) Add logging for data ingestion actions, exclusions, flags, and power analysis warnings in `code/ingest.py` and `code/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2)

**Goal**: Train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU-only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [US2] Unit test for GNN architecture constraints (layers ≤3, dim ≤128) in `tests/unit/test_model.py::test_gnn_layers_constraint`
- [ ] T022 [US2] Unit test for Integrated Gradients calculation on a dummy graph in `tests/unit/test_model.py::test_integrated_gradients_on_dummy_graph`
- [ ] T023 [US2] Integration test for training loop convergence on CPU in `tests/integration/test_training.py::test_training_converges_cpu`

### Implementation for User Story 2

- [ ] T024 [US2] (Depends on T017b) Implement `model.py`: Define lightweight GNN architecture (GCN variant, ≤3 layers, hidden dim ≤128, activation=ReLU, pooling=mean) CPU-only. **Input Shape**: `[num_nodes, num_features]`, **Output Shape**: `[num_nodes, num_classes]`. (FR-003)
- [ ] T028 [US2] (Depends on T017b, T025b OR T016b) **TRAINING**: Execute `python code/train.py --cv_strategy 5f` (or `--cv_strategy loo` if n < 150 based on T017b).
  - Check for existence of the final dataset artifact (T025b if augmented, T016b if not).
  - **Dependency Logic**: This task runs after T017b (final decision) and the appropriate dataset artifact.
  - Implement training loop with 5-fold cross-validation (or leave-one-out if n < 150) and random seed pinning.
  - Report mean macro-F1 and convergence check (loss delta < 5% over last 5 epochs).
  - **Verification**: If `|loss_t - loss_{t-5}| / loss_{t-5} >= 0.05`, raise `ConvergenceError` and exit.
  - **Checkpoint**: Save model to `data/reports/model_best.pth`. (FR-003, US-2 Scenario 1)
- [ ] T029 [US2] (Depends on T028) Implement `model.py`: Compute feature importance scores using Integrated Gradients on the trained model. **Output**: Save to `data/reports/ig_attribution_maps.json` with schema: `[{"atom_index": int, "feature_importance": float, "normalized_score": float}]`. (FR-005)
- [ ] T029b [US2] (Depends on T029) **NULL DISTRIBUTION GENERATION (ALL MOTIFS)**: Implement `evaluate.py`: Generate the null distribution for motif significance testing for **ALL identified structural motifs** by shuffling input motifs (shuffling edge features of identified motifs) repeatedly (1000 permutations, SEED=42). **Algorithm**: For each top motif identified in T029, randomly permute the **values of the edge feature vector** for that motif while preserving the `edge_index` array (topology) and node features for non-motif bonds. Then re-evaluate the model on the permuted graph to generate the null distribution. **Library**: Use `numpy.random.shuffle` and `scipy.stats.chi2`. **Output**: Save to `data/reports/null_distribution.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}`.
  - **Verification**: Verify `data/reports/null_distribution.json` exists and contains keys `bins`, `counts`, `p_value`. (FR-006, SC-002, SC-005)
- [ ] T030a [US2] (Depends on T001a) **MANUAL CURATION SIMULATION**: Implement `evaluate.py`: Generate a 'Manually Curated Proxy' subset of ≥10 hydrolysis cases using rule-based logic (as per Plan "Rule-Based Curation") to simulate a human curator.
  - **Logic**: Select a representative subset of records with high-confidence synthetic hydrolysis labels. **Rule**: `if "ester" in smiles and "aromatic" in smiles: label="hydrolysis"`. Manually verify (via code assertions) that their synthetic labels match the topological rules.
  - **Output**: Save to `data/processed/synthetic_curated_subset.json` with explicit flag `synthetic_curated=true` and `manual_verification_passed=true`. (SC-005, Plan Correction)
- [ ] T030b [US2] (Depends on T029) **TOPOLOGICAL CONSISTENCY CHECK**: Implement `evaluate.py`: Verify the consistency of synthetic labels against topological rules.
  - **Logic**: For each synthetic label, verify that the corresponding topological features (e.g., ester bond presence) are present in the graph.
  - **Output**: Save to `data/reports/topological_consistency.json` with schema: `{"consistency_score": float, "passed": bool}`. (SC-005, Plan Correction)
- [ ] T030 [US2] (Depends on T030a, T030b, T029b) **ESTER ATTRIBUTION VALIDATION**: Implement `evaluate.py`: Calculate percentage of hydrolysis cases where ester bonds are in the highest-ranked attribution scores.
  - **Traceability**: The value '10' is derived from the Plan's "Rule-Based Curation" section.
  - **Validation**: Compare this percentage against the null distribution generated by T029b. **Threshold**: `PERCENTAGE_THRESHOLD = 0.90`. **Verification**: PASS if `observed_percentage >= 0.90 AND p_value < 0.05`. Generate `data/reports/ester_attribution_check.json` with keys `{"percentage": float, "threshold": float, "p_value_null_comparison": float, "status": "PASS|FAIL"}`.
  - **Verification**: Verify `data/reports/ester_attribution_check.json` exists and `status` is either PASS or FAIL. (SC-005, Plan Correction)
- [ ] T031 [US2] (Depends on T030) Implement `evaluate.py`: Save model checkpoints, validation metrics (macro-F1), and IG attribution maps to `data/reports/`. (FR-003, FR-005)
- [ ] T032 [US2] (Depends on T031) Implement `evaluate.py`: Generate test-set predictions using the trained model; save predictions to `data/reports/test_predictions.json` for downstream validation. (FR-007)
- [ ] T033 [US2] (Depends on T017b OR T025b) Add logging for training progress, validation scores, augmentation stats, and runtime constraints in `code/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Motif Reporting (Priority: P3)

**Goal**: Receive a statistical report confirming that the identified structure-mechanism correlations are significant (via χ² test) and listing a limited set of the most prominent structural motifs.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a p-value from the χ² test and a ranked list of motifs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [US3] Unit test for permutation test logic (shuffling motifs) in `tests/unit/test_evaluate.py::test_permutation_test_shuffling`
- [ ] T035 [US3] Unit test for motif extraction and ranking logic in `tests/unit/test_evaluate.py::test_motif_extraction_ranking`
- [ ] T036 [US3] Integration test for full report generation pipeline in `tests/integration/test_reporting.py::test_full_report_generation`

### Implementation for User Story 3

- [ ] T037 [US3] (Depends on T031, T029b) **SCIENTIFIC VALIDATION (χ² Test - Primary)**: Execute `python code/evaluate.py --test chisquare --method scipy.stats.chi2`.
  - **Motif Extraction**: Use RDKit to find subgraphs of **small size** targeting **ester bonds** specifically using SMARTS patterns.
  - **Statistic Definition**: `observed_stat` = mean(macro-F1_original - macro-F1_masked). Masking method: Zero out the edge features of identified motif edges and re-evaluate.
  - **χ² Test**: Perform a χ² statistical test comparing the observed motif importance against the null distribution generated by T029b (1000 permutations, SEED=42).
  - **Binning**: Apply 'quantile-based binning' (top quantile vs rest) on absolute Integrated Gradients scores.
  - **Tie-Breaking**: If a score is at a low percentile threshold, assign it to the 'Low' bin.
  - **Validation**: Log bin counts and verify distribution is uniform before proceeding.
  - **Mapping**: Explicitly document that 'χ² Test' implements the 'shuffling input motifs' requirement from US-3 Scenario 1 for all motifs.
  - Generate `data/reports/chisquare_validation_results.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}`
  - **Verification**: Verify `data/reports/chisquare_validation_results.json` exists and contains `p_value`. (FR-006, SC-002, US-3 Scenario 1, SC-005)
- [ ] T037b [US3] (Depends on T031) **LABEL-SHUFFLING VALIDATION**: Implement `evaluate.py`: Perform a label-shuffling permutation test to validate global model significance.
  - **Verification**: Verify that label-shuffling produces a p-value > 0.05 (indicating the model is not learning random noise).
  - **Note**: This is a complementary test and does NOT satisfy FR-006's specific motif-shuffling requirement (handled by T037). (Complementary to T037)
- [ ] T038 [US3] (Depends on T031) **CONSTITUTIONAL VALIDATION (Score Distribution Check)**: Implement `code/evaluate.py`: Validate the **uniformity of the binned distribution** of Integrated Gradients scores as a prerequisite quality check.
  - **Logic**: Apply the same quantile-based binning used in T037 to the raw IG scores. Calculate the expected count for each bin assuming a uniform distribution. Compute the χ² statistic comparing observed bin counts vs expected uniform counts.
  - **Purpose**: This ensures the binning process itself is not biased before T037 uses these bins to test association significance. It validates the *distribution of scores* (binning uniformity), not the *association strength*.
  - **Output**: Generate `data/reports/ig_score_distribution_check.json` with schema: `{'bin_id': [int], 'observed_count': [int], 'expected_count': [float], 'chi_sq_stat': float, 'p_value': float, 'status': 'PASS|FAIL'}`. (Constitution VI, Plan Complexity Tracking)
- [ ] T039 [US3] (Depends on T037, T038, T031) Implement `evaluate.py`: Aggregate feature importances to identify a small set of top structural motifs and their correlation with degradation types. **Logic**: Group by motif pattern, calculate mean importance, rank by mean importance, select top few. Merge results with T037 p-values and T038 distribution check status. (FR-007)
- [ ] T040 [US3] (Depends on T039, T037, T031) Implement `evaluate.py`: Generate final report in `data/reports/` including p-values, motif list, and confidence flags (FR-007). **Content**: `p_value`, `motif_list` (top 3-5), `confidence_flags` (predictions < 0.6).
- [ ] T041 [US3] (Depends on T031) Implement `evaluate.py`: Add logic to flag predictions with confidence below a defined threshold as "low confidence" in the report. (US-3 Acceptance Scenario 3, Plan: Data Exclusion)
- [ ] T042 [US3] (Depends on T031) Add logging for statistical test results and report generation in `code/evaluate.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Generate `README.md` in repository root with usage examples, setup instructions, and data schema sections
- [ ] T044 [P] Generate `docs/usage.md` with detailed API and script documentation
- [ ] T045 [P] Refactor `code/utils.py` to ensure shared utilities are modular and tested
- [ ] T046 [P] Refactor `code/data_models.py` to ensure data classes are robust and validated
- [ ] T047 [P] Implement memory monitoring utility in `code/utils.py`
- [ ] T048 [P] Integrate subsampling trigger in `code/preprocess.py` if memory > 7GB
- [ ] T049 [P] Additional unit tests for edge cases in `tests/unit/`: `test_invalid_smiles_raises`, `test_empty_dataset_raises`
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline executes within 6 hours
- [ ] T055 [US3] **CONFIDENCE INTERVAL ESTIMATION**: Implement `code/evaluate.py` to:
  - Calculate confidence intervals for the macro-F score and the motif importance scores using bootstrapping with a sufficient number of resamples.
  - Include these intervals in the final report (`data/reports/final_report.md`) to provide a measure of uncertainty for the key metrics.
  - **Deliverable**: Generate `data/reports/confidence_intervals.json` with schema `{metric: float, ci_lower: float, ci_upper: float}`.
  - **Verification**: Verify file exists and schema matches. (US-3 Scenario 1, SC-002)
- [ ] T056 [P] **DATA VISUALIZATION**: Implement `code/visualize.py` to:
  - Generate visualizations of the molecular graphs with highlighted atoms/bonds based on Integrated Gradients scores.
  - Create plots of the permutation test results (null distribution vs. observed statistic).
  - **Deliverable**: Save `data/reports/ig_attribution_plot.png` and `data/reports/null_distribution_plot.png`.
  - **Verification**: Verify files exist and are non-empty. (FR-007, US-3 Goal)

---

## Revision Concerns & Additional Tasks

**Purpose**: Address specific gaps identified in the plan regarding data source reliability, API robustness, and statistical rigor.

### Implementation for Revision Concerns

- [ ] T053 [US3] **STATISTICAL POWER ANALYSIS ENHANCEMENT**: **REMOVED**. This logic is now fully covered by T017a, T017b, T017c.
- [ ] T054 [US3] **MOTIF SIGNIFICANCE VALIDATION**: **REMOVED**. This logic is now fully covered by T037 (χ² test) and T037b (label shuffling).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T017b output)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model outputs from US2 (T031)

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
Task: "Unit test for SMILES validation and RDKit graph conversion in tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid"
Task: "Unit test for missing data exclusion logic in tests/unit/test_preprocess.py::test_missing_env_excludes_record"

# Launch implementation tasks for User Story 1 together (if dependencies allow):
Task: "Implement ingest.py: Download records..."
Task: "Implement preprocess.py: Convert SMILES to molecular graphs..."
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
  - Developer B: User Story 2 (Model Training) - *Wait for T017b output*
  - Developer C: User Story 3 (Validation) - *Wait for T031 output*
3. Stories complete and integrate independently

---

## Methodological Corrections

**⚠️ MANDATORY INSTRUCTIONS FOR IMPLEMENTERS**

The following rules override any conflicting instructions in `spec.md` or previous drafts. These are the **only** valid instructions for this project:

1. **Data Handling Distinction**:
  - **Missing Labels**: Records missing 'degradation pathway' labels MUST be **APPLIED** with synthetic labels (hydrolysis, [deferred] oxidation, [deferred] photolysis) and INCLUDED in the training set. This satisfies FR-001 and US-1 Scenario 4.
  - **Missing Environmental Data**: The project MUST implement **IMPUTATION** of records with missing temp/pH/UV using documented defaults (pH 7, 25°C) as per FR-002. Exclusion is a secondary option only if imputation is impossible.
2. **Augmentation Strategy**:
  - **Edge Dropout**: **MANDATORY**. FR-004 mandates 'edge dropout and subgraph sampling'. The plan MUST implement these methods.
  - **T025**: Use 'edge dropout' and 'subgraph sampling' as the final augmentation method.
3. **Statistical Validation**:
  - **T037**: Implement 'χ² statistical test' specifically for **all identified motifs** to satisfy FR-006 and SC-005. This is the primary validation method for motif significance.
  - **T038**: Implement a complementary check on score distribution (binning uniformity). This is the constitutional/quality check.
4. **Thresholds**: For SC-004, trigger a warning if n < 150. For SC-005, use `THRESHOLD_TOP_PERCENT` (default **a top-tier percentile**) and `PERCENTAGE_THRESHOLD` (default 0.90) for verification. For US-3, use `CONFIDENCE_THRESHOLD` (default set to a moderate level).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion must use real URLs; synthetic data is the primary fallback for ALL runs if APIs fail.
- **CRITICAL**: Records with missing environmental data (temp/pH/UV) MUST be FLAGGED then IMPUTED (DEFAULT PATH) using documented defaults.
- **CRITICAL**: Records with missing labels MUST be FLAGGED for curation then APPLIED with synthetic labels (FR-001), EXCEPT if ALL records are missing, in which case the system MUST HALT (FR-008).
- **CRITICAL**: GNN must run on CPU only; no CUDA/GPU dependencies.
- **CRITICAL**: Edge Dropout (T025) is the ONLY augmentation method as per FR-004.
- **CRITICAL**: χ² Test (T037) is the Primary/Scientific validator; T038 is Complementary/Constitutional (Score Distribution Check).
- **CRITICAL**: Confidence threshold < `0.6` is MANDATORY for flagging low-confidence predictions (US-3 Scenario 3, Plan).
- **CRITICAL**: T017a, T017b, T017c atomize the power analysis logic and amendment ratification for deterministic execution.
- **CRITICAL**: T029b generates the null distribution locally in Phase 4 to allow T030 to run independently.
- **CRITICAL**: T037 is the primary satisfier of FR-006 and SC-005; T037b is complementary.
- **CRITICAL**: All tasks marked [X] are fully defined and ready for execution; downstream dependencies are guaranteed to have valid producers.
- **CRITICAL**: T053, T054 have been removed to avoid redundancy with T017a-b and T037.
- **CRITICAL**: T055 and T056 enhance statistical rigor and interpretability.
- **CRITICAL**: T017b ensures the LOO switch decision is made on the pre-augmentation dataset size.
- **CRITICAL**: T019 and T028 dependencies are updated to handle conditional artifacts (T025b or T016b).