---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Surface Area from Graph Convolutional Networks

**Input**: Design documents from `/specs/001-predicting-molecular-surface-area/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and schema generation.

- [ ] T001-Setup-Script [P] Initialize all project directories. Create a Python script `scripts/setup_dirs.py` that generates the following directories: `code/`, `code/data/`, `code/models/`, `code/eval/`, `code/utils/`, `tests/contract/`, `tests/unit/`, `tests/integration/`, `results/reports/`, `results/plots/`, `results/baseline/`, `results/predictions/`, `logs/`, `data/raw/`, `data/processed/`, `data/splits/`, and `data/schemas/`. **Output**: `scripts/setup_dirs.py`.
- [ ] T001-Setup-Execute [P] Execute the setup script. Run: `python scripts/setup_dirs.py` from the repository root. **Context**: This task must run after T001-Setup-Script. **Command**: Run `python scripts/setup_dirs.py` from the repository root. **Output**: All listed directories created.
- [X] T002 [P] Create `code/requirements.txt` containing pinned versions of: `rdkit==2023.9.5`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `pyyaml==6.0.1`, `numpy==1.26.2`, `pytest==7.4.3`, `ruff==0.1.6`, `black==23.11.0`, `datasets==2.15.0`, `huggingface_hub==0.19.4`.
- [ ] T002-Install [P] Install dependencies. Run: `pip install -r code/requirements.txt` followed by `pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu` and `pip install torch-geometric==2.4.0 --index-url https://download.pytorch.org/whl/cpu`. Do not use `torch (cpu)` as a package name. **Context**: These commands MUST be run inside the virtualenv created by T001-Setup-Execute.
- [X] T002b [P] Create `code/config.py` and define `TIME_BUDGET` (float, hours) set to 6.0 (value from Plan.md 'Performance Goals'), `MAX_RAM_GB` (float) set to 7.0, `RANDOM_SEED` (int) set to 42, `MAX_MOLECULES` (int) set to [deferred] (to be resolved by pilot study or config override), and SENSITIVITY_THRESHOLDS (list of floats) set to a range of representative low-level thresholds.. **Note**: The `SENSITIVITY_THRESHOLDS` values are explicitly set to the Spec-mandated list (FR-006, Assumptions). **Dependency**: None.
- [ ] T003a [P] Create Ruff configuration. Generate `.ruff.toml` at repository root with project-specific linting rules. **Output**: `.ruff.toml`.
- [X] T003b [P] Create Black configuration. Generate `pyproject.toml` (or `.black.toml` if preferred) with Black formatting rules. **Output**: `pyproject.toml` (Black section).
- [X] T004 [P] Generate `data/schemas/static_schema.yaml` defining the expected fields for the processed dataset (SMILES, node_features, edge_features, surface_area, molecular_weight).
- [X] T005 [P] Generate `data/schemas/model_schema.yaml` defining the expected fields for model output (model_type, metrics, hyperparameters).
- [X] T006 [P] Generate `data/schemas/sensitivity_schema.yaml` defining the expected fields for sensitivity reports (thresholds, success_rates, corrected_p_values).
- [X] T049 [P] Implement pre-flight network connectivity check in `code/utils/network_check.py`. This task must run before any ingestion tasks to verify access to ZINC15. **Failure Behavior**: If the connection to ZINC15 fails or the URL is unreachable, the function MUST raise a `ConnectionError` immediately and halt the pipeline. Do NOT retry or fall back to synthetic data.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes robustness features (memory, network, batch sizing) to ensure the pipeline runs successfully.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/__init__.py` and environment configuration loader
- [X] T008a [P] Setup logging infrastructure in `code/utils/logging.py`
- [X] T009a [P] Create base data model `Molecule` in `code/data_models/molecule.py`. **Attributes**: `smiles` (str), `mol` (rdkit.Chem.Mol), `molecular_weight` (float), `atom_count` (int), `node_features` (np.ndarray), `edge_features` (np.ndarray). **Methods**: `validate()`, `to_dict()`. **Node Features**: Must be explicitly defined as `[atom_type, hybridization, formal_charge]`. **Edge Features**: Must be explicitly defined as `[bond_type, conjugated, aromatic]`. **Dependency**: None.
- [X] T009b [P] Create base data model `Graph` in `code/data_models/graph.py`. **Attributes**: `nodes` (list), `edges` (list), `node_features` (np.ndarray), `edge_features` (np.ndarray), `adjacency_matrix` (np.ndarray). **Methods**: `to_pyg_format()`, `validate()`. **Dependency**: None.
- [X] T009c [P] Create base data model `EvaluationResult` in `code/data_models/evaluation_result.py`. **Attributes**: `model_type` (str), `mae` (float), `rmse` (float), `r2` (float), `predictions` (list), `errors` (list). **Methods**: `to_json()`, `summary()`. **Dependency**: None.
- [X] T010 [P] Implement seed pinning utility for reproducibility in `code/utils/seed.py`. **Implementation**: Set `RANDOM_SEED` from `code/config.py` (value 42).
- [X] T011 [P] Setup dataset checksumming utility in `code/utils/checksum.py`
- [X] T017 [P] Implement SMILES validation utility in `code/utils/validators.py`. This utility MUST validate SMILES syntax and return a list of invalid strings. It must be used by T048 and T014. **Output**: `code/utils/validators.py` containing `validate_smiles(smiles_list)` function.
- [X] T018 [P] Implement logging infrastructure for excluded molecules and dataset statistics in `code/utils/logging.py` (extending T008a). This utility MUST handle JSON logging for excluded molecules to `logs/excluded_molecules.log` and `logs/ingestion_errors.log`. **Output**: `code/utils/logging.py` with `def log_excluded_molecules(count: int, smiles_list: List[str]) -> None` and `def log_errors(errors: List[Exception]) -> None` functions. **Note**: The `log_errors` function MUST log invalid SMILES at the WARNING level.
- [X] T045 [P] Implement memory-profiling wrapper in `code/utils/memory_monitor.py`. This wrapper MUST log peak RAM usage per epoch for training loops. If memory usage exceeds `MAX_RAM_GB` (from `code/config.py`), it must trigger an early exit with a diagnostic report. **Output**: `code/utils/memory_monitor.py` with `MemoryMonitor` class.
- [X] T056 [P] Implement robust `load_dataset` wrapper in `code/data/ingest.py` that strictly adheres to the "Fail Loudly" principle. This wrapper MUST remove any `try/except` blocks that catch network errors and fall back to synthetic data. If the real ZINC15 stream fails, it MUST raise `ConnectionError` or `ValueError` immediately.
- [X] T057 [P] Implement checksum verification in `code/data/ingest.py`. This task MUST calculate the SHA-256 hash of each downloaded chunk and compare it against a known manifest (if available) or log the hash to `data/raw/checksums.json` for reproducibility. **Action**: This task MUST run unconditionally on the raw dataset, regardless of manifest availability. **Failure Behavior**: If a manifest exists and the calculated hash mismatches, the task MUST halt with a critical error. If no manifest is available, log the hash to `data/raw/checksums.json`. **Dependency**: T056.
- [X] T058 [P] Implement dynamic batch size fallback in `code/models/train.py`. If the initial batch size causes an OOM error, the system MUST automatically reduce the batch size by half and retry, logging the adjustment, rather than crashing immediately (provided batch size >= 1).
- [X] T059 [P] Create a placeholder for limitations reporting in `code/eval/sensitivity.py` to be populated by T030. **Output**: `code/eval/sensitivity.py` with a function `generate_limitations_section(sample_size: int, streaming_rule: str) -> str`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest SMILES, convert to 2D graphs, generate 3D SASA labels, and split data.

**Independent Test**: A researcher can run the data pipeline script and verify that a CSV/Parquet file is produced containing SMILES, node/edge feature matrices, and a numeric surface area column, with no missing values in the target column for the training set.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py` validating against `data/schemas/static_schema.yaml` (generated by T004) to ensure input format compliance before processing.
- [X] T013 [P] [US1] Integration test for SMILES ingestion pipeline in `tests/integration/test_ingest.py` (must run after T048)

### Implementation for User Story 1

- [X] T048 [US1] Implement SMILES ingestion from ZINC15 using `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM. Fetch and process molecules in fixed-size chunks. **Strict Source Logic**: Check `DATA_SOURCE_OVERRIDE` environment variable. If present, use that source exclusively. If absent, fetch ONLY from ZINC15. Raise a critical error if the source is invalid or inaccessible. **Max Atoms Filter Implementation**: Calculate the number of atoms for each molecule using RDKit. If the atom count is > 100, exclude the molecule from the dataset and log the specific SMILES string to `logs/excluded_molecules.log` using T018. **Invalid SMILES Handling**: Use T017 to catch syntax errors during parsing. **Log invalid SMILES to `logs/ingestion_errors.log` at the WARNING level** using T018. Validate syntax. **Schema Validation**: Validate against `data/schemas/static_schema.yaml` AND verify that the dataset contains the necessary fields or metadata to support 3D conformer generation (e.g., valid valence, atom types) to ensure downstream T015 will succeed. **Chunk Integrity**: After processing each chunk, verify that the number of rows in the output parquet matches the number of valid molecules in the input chunk (minus excluded ones). If the count is inconsistent, raise an error. The output will be written to `data/raw/chunk_*.parquet`. **Dependency**: T017, T018, T008a, T049.
- [ ] T014-Sample [US1] Implement dataset sampling and power reporting. **Action**: Read `data/raw/chunk_*.parquet`. **Pilot Study Step**: Run a pilot on a small representative subset (e.g., a limited number of molecules) to estimate runtime per molecule. Calculate `MAX_MOLECULES` such that total estimated runtime < 5.5 hours. If the total count exceeds `MAX_MOLECULES` (defined in `code/config.py` as [deferred]), select a random sample of exactly `MAX_MOLECULES` using `RANDOM_SEED`. If the count is below the limit, use all data. **Fallback Logic**: If `MAX_MOLECULES` is [deferred], skip sampling and use all available data, logging a note in `sampling_report.json` explaining the statistical power limitation of the full dataset. **Output**: `data/processed/sampled_dataset.parquet` and `data/processed/sampling_report.json` containing keys `total_available`, `sampled_count`, `sample_seed`, and `power_limitation_note` (text explaining the statistical power limitation of the sample size). **Dependency**: T048.
- [ ] T014-Gate [US1] **Verify Atom Count Exclusion Rate**: Calculate the total number of molecules excluded by the >100 atom filter (from T048) and compare to the total input count. **Action**: If the exclusion rate is > 50%, generate `data/processed/atom_count_success_report.json` and log a WARNING, but DO NOT halt. If the total remaining count is < 1000, generate `data/processed/atom_count_failure_report.json` and halt with a CRITICAL error. Otherwise, proceed. **Output**: `data/processed/atom_count_success_report.json` (if rate > 50%) or `data/processed/atom_count_failure_report.json` (if count < 1000) or success log. **Dependency**: T048.
- [ ] T014 [US1] 2D graph feature extraction (atom type, hybridization, charge) using RDKit in `code/data/preprocess.py`, and **calculate Molecular Weight** for each molecule. **Explicit Action**: Implement a filter to exclude molecules with >100 atoms BEFORE outputting the file, logging the count of excluded molecules to `logs/excluded_molecules.log` using T018. **Order**: Filter Molecules -> Extract 2D Features -> Calculate MW. **Merge T014b**: This task now includes the Molecular Weight calculation previously in T014b. **Embed Conformer Params**: Load `data/processed/conformer_params.json` (generated in T015a) and embed its content as a JSON string into the `conformer_config_hash` metadata field of the Parquet file to satisfy the 'Single Source of Truth' principle. **Output**: `data/processed/graphs_with_features.parquet`. **Output Schema**: The Parquet file MUST contain columns: `smiles` (string), `node_features` (list of lists), `edge_features` (list of lists), `molecular_weight` (float), and metadata `conformer_config_hash`. **Dependency**: T014-Sample -> T014-Gate -> T014 -> T015a (strictly sequential). **Note**: This task must run after T014-Sample, T014-Gate, and T015a (to get params for embedding).
- [ ] T015a [US1] 3D conformer generation (ETKDG) and failure logging in `code/data/preprocess.py`. **Explicit Parameter Logging**: Generate `data/processed/conformer_params.json` explicitly within this task. **JSON Schema**: The file MUST contain keys `numThreads` (int), `maxAttempts` (int), `energyMinimizationSteps` (int), and `random_seed` (int) to satisfy Constitution Principle VII. **Generate `data/processed/failure_report.csv`** with columns `[smiles, failure_reason, atom_count, numThreads, maxAttempts, energyMinimizationSteps, random_seed]` for any failed conformers. **Schema**: `failure_reason` must be a string enum with the following EXACT values: 'ETKDG_FAIL', 'MINIMIZATION_FAIL', 'INVALID_VALENCE', 'CONFORMER_GENERATION_FAIL', 'UNKNOWN_FAIL'. **Mapping Logic**: Map RDKit exceptions to these codes deterministically: `ValueError` (valence issues) -> 'INVALID_VALENCE'; `RuntimeError` (ETKDG failure) -> 'ETKDG_FAIL'; `RuntimeError` (minimization failure) -> 'MINIMIZATION_FAIL'; `RDKitException` (generic RDKit error) -> 'CONFORMER_GENERATION_FAIL'; Any other exception -> 'UNKNOWN_FAIL'. **Global Failure Rate Logic**: Maintain a running count of `total_attempted` and `total_failed` across ALL processed chunks. After processing each chunk, calculate `global_failure_rate = total_failed / total_attempted`. **Halt Logic**: If `global_failure_rate` > 0.10, generate `data/processed/failure_report.csv` and THEN halt with a critical error. Log failure counts to `logs/conformer_failures.log`. **Output**: `data/processed/conformers.parquet` containing SMILES and the generated conformer objects (or serialized coordinates). **Dependency**: Must run after T014-Gate (to ensure dataset is validated) and T048 (SMILES source). **Note**: T015a does NOT depend on T014 (2D features) for generation, but T014 depends on T015a for params. **Status**: Active.
- [ ] T015b [US1] Calculate SASA and 3D geometric descriptors in `code/data/preprocess.py`. **Action**: Load conformers from T015a. Calculate SASA using RDKit. Calculate the following 3D geometric descriptors from the generated conformers: `radius_of_gyration`, `principal_moment_1`, `principal_moment_2`, `principal_moment_3`, and `sasa_components`. **Output**: `data/processed/descriptors.parquet` containing SMILES, `surface_area`, and the calculated 3D descriptors. **Dependency**: T015a.
- [ ] T015d [US1] **Conformer Noise Check**: Generate multiple conformers for a representative subset of molecules (e.g., a sample set). using the parameters from T015a. Calculate the SASA variance across these conformers for each molecule. **Action**: Verify that the primary sensitivity thresholds (from T002b) are significantly larger than the calculated noise floor (variance). **Output**: `data/processed/noise_floor_report.json` containing `mean_variance`, `max_variance`, and `threshold_validation` (boolean). **Dependency**: T015a.
- [ ] T015c [US1] Merge artifacts and embed hashes in `code/data/preprocess.py`. **Action**: Merge `graphs_with_features.parquet` (T014), `conformers.parquet` (T015a), and `descriptors.parquet` (T015b) into `data/processed/paired_dataset.parquet`. **Verification**: Ensure `data/processed/conformer_params.json` exists and contains keys `numThreads`, `maxAttempts`, `energyMinimizationSteps`, `random_seed`. Ensure `data/processed/paired_dataset.parquet` contains the `surface_area` column with no NaN values and the required 3D descriptors. **Conformer Linkage**: Compute a SHA-256 hash of the `conformer_params.json` content and embed it as a `conformer_config_hash` in the Parquet file's metadata and as a new column in the dataset to ensure the 'Single Source of Truth' principle is met. **Dependency**: T014, T015a (SUCCESS STATE ONLY), T015b, T015d. **Note**: This task must not run if T015a failed.
- [ ] T016 [US1] Implement data splitting logic (stratified by Molecular Weight) generating `data/splits/train_indices.csv`, `data/splits/test_indices.csv`, and `data/splits/split_report.json`. **Dependency**: Must run after T014 (to ensure MW values are available). **Execute the Kolmogorov-Smirnov (KS) test** comparing the `molecular_weight` column of the training set vs the test set. **Output**: **ALWAYS** generate `data/splits/split_report.json` containing the key `ks_p_value` and `used_seed` (the integer seed used for this split), even if the p-value is <= 0.05. If p <= 0.05, also generate `data/splits/split_error_report.json` with details. **Failure Handling**: If p <= 0.05, the `split_report.json` must still be generated with the `used_seed` to allow T016-Gate to retry. **Note**: This task does NOT depend on T015 (SASA generation) as stratification relies solely on MW. **Dependency**: T014.
- [ ] T016-Gate [US1] **Verify Split Report**: Load `data/splits/split_report.json` and verify that `ks_p_value` > 0.05. **Action**: If the condition is not met, retry the split with a new random seed up to 5 times. **Initial Seed**: The initial seed for the first attempt is `RANDOM_SEED` from `code/config.py` (a fixed integer value). The new seed for each retry is generated by **incrementing the `used_seed` from the report by 1** (e.g., if the initial attempt used seed S and failed, the first retry uses S+1). **Retry Logic**: The initial seed for the retry loop is explicitly `current_used_seed + 1`. If all retries fail, generate `data/splits/split_failure_report.json` with details of the best p-value achieved, log a CRITICAL error, and proceed with the best-effort split (do NOT halt). **Output**: If successful, log a confirmation message; if failed, log the error and proceed. **Dependency**: T016.
- [ ] T016-Report [US1] **Report Final Dataset Statistics**: Calculate and report the final dataset size after all filtering steps (T048, T015a). **Action**: Count the number of molecules in `data/processed/paired_dataset.parquet` and `data/splits/train_indices.csv` / `data/splits/test_indices.csv`. **Output**: `data/processed/final_dataset_stats.json` containing keys `total_molecules`, `train_count`, `test_count`, `excluded_by_atom_count`, `excluded_by_conformer_failure`. **Dependency**: T015c, T016-Gate.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GCN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight CPU-tractable GCN and a Baseline on 2D descriptors, then compare performance.

**Independent Test**: The training script runs to completion within the CI limit, producing two model artifacts and a results report showing MAE, RMSE, R² for both, along with a statistical significance test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py` validating against `data/schemas/model_schema.yaml` (generated by T005)
- [X] T020 [P] [US2] Integration test for training loop and early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T021a [US2] Implement lightweight GCN model definition (PyTorch Geometric, CPU-only) in `code/models/gcn.py` containing class `GCNModel` with `forward(input_tensor)` method
- [ ] T021c [US2] **Train Geometry-Based Baseline**: Train a Random Forest model on **geometric descriptors** (from T015b: `radius_of_gyration`, `principal_moments`, `sasa_components`) using `code/models/baseline.py`. This serves as the **Geometry-Based Baseline** required by FR-004 and FR-005 to compare 2D topology against a 3D-derived predictive model. **Training**: Train on the **training split** (from T016). **Inference Pipeline**: For the **test split**, regenerate 3D conformers using parameters from `data/processed/conformer_params.json` (T015a) and calculate 3D descriptors on-the-fly. **Clarification**: This is a TRAINED MODEL, distinct from the Geometry Oracle. The descriptors used are derived from RDKit's 3D conformer generation, satisfying the "Geometry-Based" requirement. The test set conformers are regenerated using the *same* single-conformer logic as T015a (not multiple conformers); the 'Conformer Noise Check' (T015d) is a separate task for the training set validation. **Input**: `data/processed/descriptors.parquet` (train split) and regenerated descriptors for test split. **Output**: `results/baseline/baseline_3d.pkl` and `results/predictions/baseline_3d_predictions.parquet` containing columns `[smiles, predicted_sasa, error]`. **Dependency**: Must run after T016 (split indices), T015b (3D descriptors for training), and T015a (for parameters). **Note**: This task implements the required Geometry-Based Baseline per FR-004 and Plan Phase 3 Step 5.
- [ ] T022 [US2] Implement training loop with early stopping (patience=5, max 50 epochs) in `code/models/train.py`, incorporating gradient accumulation logic (merged from T050). **Output**: `results/predictions/gcn_predictions.parquet` containing columns `[smiles, predicted_sasa, error]`. **Verification**: Ensure `results/predictions/gcn_predictions.parquet` exists with the specified columns. **Dependency**: Must run after T021a and T016.
- [ ] T023a [US2] Implement MAE calculation function in `code/eval/metrics.py`. **Signature**: `def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float`. **Dependency**: T010.
- [ ] T023b [US2] Implement RMSE calculation function in `code/eval/metrics.py`. **Signature**: `def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float`. **Dependency**: T010.
- [ ] T023c [US2] Implement R² calculation function in `code/eval/metrics.py`. **Signature**: `def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float`. **Dependency**: T010.
- [ ] T040 [US2] **Calculate Model Performance Metrics**: Compute aggregate metrics (MAE, RMSE, R²) for the GCN model (from T022) and the **Geometry-Based Baseline (from T021c)** on the test set. **Output**: `results/reports/model_metrics.json` containing keys `gcn_mae`, `baseline_3d_mae`, `gcn_r2`, `baseline_3d_r2`. **Verification**: Ensure the JSON file exists and contains the specified keys. **Note**: This task calculates aggregate metrics for the required models. **Dependency**: Must run after T022 and T021c.
- [ ] T025 [US2] Integrate training and evaluation to produce final comparison report generating `results/reports/model_comparison.json`. **Verification**: Ensure the JSON file exists and contains keys `gcn_mae`, `baseline_3d_mae`, `gcn_r2`, `baseline_3d_r2`, `p_value`, and `cohen_d`. Explicitly calculate and report the raw MAE, RMSE, and R² for the GCN (T022) and the **Geometry-Based Baseline (T021c)**. **Primary Comparison**: Perform a **paired t-test** comparing the prediction errors of the GCN model (T022) and the **Geometry-Based Baseline (T021c)**. This comparison satisfies Spec FR-005 and US-2 by comparing two predictive methods (GCN vs Geometry-Based Baseline). **Note**: This task explicitly compares GCN (T022) against T021c (Geometry-Based Baseline). **Dependency**: Must run after T022 and T021c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on MAE thresholds (absolute only) and apply multiple-comparison corrections.

**Independent Test**: The analysis script re-runs the evaluation with modified thresholds and generates a report showing how success rates change, including corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_report.py` validating against `data/schemas/sensitivity_schema.yaml` (generated by T006)
- [ ] T027 [P] [US3] Unit test for Bonferroni/FDR correction logic in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement sensitivity analysis script sweeping absolute MAE thresholds across a range of low to moderate magnitudes. (as mandated by Spec FR-006 and Assumptions, overriding Plan Phase 4 Step 4 which contains an error) in `code/eval/sensitivity.py`. **Dependency**: Must run after T022 (GCN Predictions) and T021c (Geometry-Based Baseline Predictions). **Action**: Load per-molecule predictions from `results/predictions/gcn_predictions.parquet` and `results/predictions/baseline_3d_predictions.parquet`. **Input Schema**: The input files MUST contain a column named `error` (float, unit: Å²) (as generated by T022 and T021c). **Action**: Calculate success rates for each threshold. **Success Rate Formula**: `success_rate = count(errors < threshold) / total_count`, where `total_count` is the number of molecules in the test set with valid predictions (excluding any where conformer generation failed). **Output**: `data/processed/sensitivity_absolute.csv`. **Output Schema**: The CSV file MUST contain columns: `threshold` (float), `success_rate` (float, 0.0-1.0), `sample_size` (int). **Primary Verification**: This is the mandatory verification path per Spec FR-006. The report must explicitly state that this is the primary metric and justify the threshold choice against experimental error. **Verification**: Verify that the sum of success_rate across thresholds is not used for aggregation, but each is reported independently. **Note**: The Plan.md FR/SC Coverage Map and this Task are aligned to use Spec-compliant thresholds of varying magnitudes.. **Clarification**: This task implements absolute thresholds within a range of low to moderate magnitudes (e.g., 0.05, 0.1) Å².. No relative threshold sweep is implemented or referenced. **Dependency**: T002b (import `SENSITIVITY_THRESHOLDS` from `code/config.py`).
- [ ] T029 [US3] Implement multiple-comparison correction (Bonferroni or FDR) for threshold sweep results in `code/eval/sensitivity.py`. **Condition**: Apply correction **whenever** multiple tests (n > 1) are performed, as mandated by Spec FR-007. **Method Selection**: If `n <= 5`, use Bonferroni correction; if `n > 5`, use False Discovery Rate (FDR) correction. Specify the chosen method and the condition in the output report. **Target**: Apply the correction **only** to the p-values generated by the **McNemar's test** performed at **each threshold** in T028 (comparing GCN vs. Baseline success proportions). Each threshold represents a distinct hypothesis test (null hypothesis: no difference in success rates at that threshold). **Note**: The paired t-test from T025 is a single test comparing overall errors and does NOT require correction for multiple comparisons.
- [ ] T030 [US3] Generate sensitivity report with threshold justification and adjusted p-values writing `results/reports/sensitivity_analysis.md`. **Dependency**: Must run after T028 (Absolute), T029 (Correction), and T040 (Model Metrics). **Note**: Relative threshold sweep removed per Spec FR-006. **Justification Requirement**: The report must explicitly state the justification for the primary threshold. **Logic**: 1. If `research.md` exists and contains a relevant citation for the 0.05 Å² threshold, use that citation. 2. If `research.md` does not exist or contains no relevant citation, use the justification from the **Assumptions section of spec.md** ("typical experimental error margins in surface area measurement"). 3. The Spec Assumptions are always available, so the 'NO_CITATION_FOUND' branch is effectively removed; the report will always have a justification. **Include Power Limitation**: The report must include a "Limitations" section discussing the statistical power of the sample size (from T014-Sample) and any biases introduced by the chunked streaming process. **Dependency**: T028, T029, T040, T014-Sample.
- [ ] T031 [US3] Create visualization plots for sensitivity curves in `results/plots/`. **Library**: Use `matplotlib`. **Style**: Use `seaborn` 'whitegrid' style. **Mapping**: x-axis: threshold, y-axis: success_rate. **Verification**: Output `.png` files named `sensitivity_absolute.png`. **Dependency**: T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Schema Generation & Polish

**Purpose**: Generate missing schema files and perform final polish.

- [ ] T032a [P] Update `README.md` with project overview, installation instructions, and usage examples. **Traceability**: Document FR-001 to FR-007 in the overview. **Output**: `README.md` with a **"Traceability Matrix"** table mapping FR-001 to FR-007 to specific implementation files (e.g., FR-001 -> `code/data/ingest.py`). The table must have columns: "Requirement ID", "Description", "Implementation File", "Status". **Specific Mappings**: FR-004 -> `code/models/baseline.py` (T021c); FR-005 -> `code/eval/metrics.py` (T025).
- [ ] T032b [P] Update `docs/` with detailed API documentation for key modules (`code/data/`, `code/models/`, `code/eval/`). **Traceability**: Ensure documentation covers FR-001 to FR-007 implementation details. **Output**: `docs/` generated using **pdoc3** tool. **Command**: `pdoc3 --output-directory docs/api code`. The task must create the `docs/api/` directory if it does not exist and generate HTML files for all modules.
- [ ] T033-Refactor-Preprocess [P] Refactor `code/data/preprocess.py` to use generator expressions for memory efficiency. **Target**: Reduce peak memory usage of T014 by at least 20% compared to list-based processing. **Specific Action**: Replace list comprehensions with generator expressions in the `process_chunk` function. **Output**: Refactored `code/data/preprocess.py`.
- [ ] T033-Refactor-Train [P] Refactor `code/models/train.py` to modularize the training loop and integrate the memory monitor (T045) and dynamic batch sizing (T058). **Target**: Ensure training loop gracefully handles OOM by reducing batch size without crashing. **Specific Action**: Extract the training step into a `train_epoch` function. **Output**: Refactored `code/models/train.py`.
- [ ] T035-Test-Validators [P] Add unit tests for edge cases in `tests/unit/test_validators.py`: `test_invalid_smiles_returns_list`, `test_empty_list_returns_empty_list`, `test_mixed_valid_invalid_returns_list`. **Note**: T017 returns a list, so tests verify list content, not exceptions.
- [ ] T035-Test-Preprocess [P] Add unit tests for edge cases in `tests/unit/test_preprocess.py`: `test_conformer_failure_handling`, `test_max_atoms_filter`.
- [ ] T036 Run `quickstart.md` validation. **Criteria**: Verify FR-001 to FR-007 execution via `quickstart.md` steps.
- [ ] T052-Run [P] Execute the pipeline. **Command**: `python code/main.py --mode full --seed <random_seed>`. **Decision Logic**: Execute the pipeline on the representative subset defined in the Plan's Fallback Strategy. Measure the actual runtime. Output `results/reports/pipeline_execution.log`. **Dependency**: T016-Gate, T022, T021c.
- [ ] T052-Verify-Parse [P] Parse execution log for runtime. **Action**: Extract total runtime from `results/reports/pipeline_execution.log`. **Output**: `results/reports/runtime_raw.json`. **Dependency**: T052-Run.
- [ ] T052-Verify-Report [P] Generate verification report. **Action**: Compare the measured time from T052-Verify-Parse against the `TIME_BUDGET` variable in `code/config.py` (value 6.0 hours). Generate `results/reports/final_runtime_verification.md`. **Constraint**: Explicitly state that the time budget is 6.0 hours as defined in `code/config.py` and Plan.md, and verify against this concrete limit. **Include Power Limitation**: The report must include a "Limitations" section discussing the statistical power of the sample size (from T014-Sample) and reference the `sampling_report.json` from T014-Sample. **Dependency**: T052-Verify-Parse, T014-Sample.

---

## Phase 7: Revision & Robustness (Post-Analysis Fixes)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` review regarding data sourcing, memory constraints, and execution reliability.
**Note**: This phase is now empty as all robustness tasks (T045, T056, T057, T058, T059) have been moved to earlier phases to ensure pipeline robustness before execution.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**IMPORTANT**: The following rules apply ONLY to **Tests** and **Independent Modules**. **Implementation tasks within User Story 1 are strictly sequential** due to data flow dependencies.

- **Tests**: All test tasks (e.g., T012, T013) for a user story marked [P] can run in parallel.
- **Independent Modules**: Tasks in different files with no data dependencies (e.g., T001-Setup-Script, T003a) can run in parallel.
- **User Story 1 (US1) Implementation**: **STRICTLY SEQUENTIAL**.
 - T048 (Ingest) -> T014-Sample -> T014-Gate -> T015a (3D Gen) -> T014 (2D Feats) -> T015b (SASA) -> T015d (Noise Check) -> T015c (Merge) -> T016 (Split).
 - **Note**: T014 (2D features) and T015a (3D conformers) CANNOT run in parallel; T014 depends on T015a for params embedding.
 - Do NOT attempt to run T014 before T014-Sample completes.
 - Do NOT attempt to run T015a before T014-Gate completes.
 - The [P] tag on US1 implementation tasks is **incorrect** and should be ignored for execution planning; rely on the explicit dependency list in each task description.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

**Clarification**: While T014 (2D features) and T015a (3D conformers) can technically run in parallel after T014-Sample (if T014 does not wait for T015a for params), T015c (Merge) is a **strict barrier** that waits for both to complete successfully. Do not assume T015c can run until both T014 and T015a are done. T014 must wait for T015a to generate params for embedding.

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

- [P] tasks = different files, no dependencies (for Tests/Setup only)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence