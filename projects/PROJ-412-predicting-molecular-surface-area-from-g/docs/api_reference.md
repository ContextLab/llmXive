# API Reference

This document provides detailed API documentation for the key modules of the `llmXive` project: `code/data/`, `code/models/`, and `code/eval/`. The implementation covers Functional Requirements FR-001 through FR-007.

## Module: `code/data/ingest.py`

Handles the ingestion of SMILES strings from ZINC15 using streaming to manage memory constraints.

### Functions

#### `fetch_zinc15_streaming()`
Fetches the ZINC15 dataset stream.
- **Behavior**: Checks `DATA_SOURCE_OVERRIDE`. If absent, fetches from ZINC15. Raises `ConnectionError` if the source is unreachable (Fail Loudly principle).
- **Returns**: Generator yielding chunks of data.

#### `process_smiles_chunk(chunk)`
Processes a single chunk of SMILES data.
- **Logic**: Validates SMILES syntax, calculates atom count, and filters molecules with >100 atoms.
- **Logging**: Logs excluded molecules to `logs/excluded_molecules.log` and invalid SMILES to `logs/ingest_errors.log`.

#### `calculate_checksum(data_chunk)`
Calculates the SHA-256 hash of a data chunk.
- **Usage**: Used to verify data integrity during ingestion.

#### `save_checksums(checksums)`
Saves calculated checksums to `data/raw/checksums.json` for reproducibility.

#### `write_chunk_to_parquet(chunk, path)`
Writes a processed chunk to a Parquet file.

---

## Module: `code/data/preprocess.py`

Handles 2D graph feature extraction, 3D conformer generation, and SASA calculation.

### Functions

#### `generate_conformer_params()`
Generates RDKit ETKDG parameters.
- **Output**: Returns a dictionary containing `numThreads`, `maxAttempts`, `energyMinimizationSteps`, and `random_seed`.
- **Traceability**: Parameters are serialized to `data/processed/conformer_params.json`.

#### `map_rdkit_exception_to_reason(exception)`
Maps RDKit exceptions to standardized failure codes.
- **Returns**: One of 'ETKDG_FAIL', 'MINIMIZATION_FAIL', 'INVALID_VALENCE', 'CONFORMER_GENERATION_FAIL'.

#### `process_molecule_3d(molecule)`
Generates a 3D conformer and calculates SASA.
- **Logic**: Uses ETKDG method. If generation fails, logs to `data/processed/failure_report.csv`.
- **Output**: Returns a dictionary with SMILES, SASA, and 3D descriptors (`radius_of_gyration`, `principal_moments`).

#### `calculate_sasa(mol)`
Calculates the Solvent Accessible Surface Area using RDKit.

#### `save_failure_report(failures)`
Writes the list of conformer failures to `data/processed/failure_report.csv`.

---

## Module: `code/data/split.py`

Implements stratified data splitting based on Molecular Weight.

### Classes

#### `SplitResult`
Dataclass holding the result of a split operation.
- **Attributes**: `train_indices`, `test_indices`, `ks_p_value`.

### Functions

#### `stratified_split_by_mw(data, test_size)`
Splits the dataset into train and test sets, stratifying by Molecular Weight.
- **Verification**: Performs a Kolmogorov-Smirnov (KS) test to ensure distributions are similar.
- **Output**: Returns a `SplitResult` object.

#### `validate_split_distribution(split_result)`
Validates that the split meets statistical requirements (p-value > 0.05).

---

## Module: `code/models/gcn.py`

Defines the Graph Convolutional Network model.

### Classes

#### `GCNModel`
A CPU-tractable GCN model using PyTorch Geometric.
- **Constructor**: `__init__(input_dim, hidden_dim, output_dim)`
- **Method**: `forward(input_tensor)`
 - **Logic**: Applies GCN convolution layers followed by global mean pooling and a linear output layer.

---

## Module: `code/models/baseline.py`

Implements baseline models for comparison (2D descriptors and 3D geometry).

### Functions

#### `extract_geometry_features(data)`
Extracts 3D geometric descriptors (`radius_of_gyration`, `principal_moments`) from the dataset.

#### `train_baseline_model(features, labels)`
Trains a Linear Regression model.
- **Input**: Numpy arrays of features and labels.
- **Output**: Fitted model and predictions.

#### `evaluate_model(model, features, labels)`
Calculates MAE, RMSE, and R² for the baseline model.

---

## Module: `code/models/train.py`

Contains the training loop with early stopping and memory monitoring.

### Classes

#### `EarlyStopping`
Implements early stopping logic.
- **Attributes**: `patience`, `min_delta`, `counter`.
- **Method**: `early_stop` property indicates if training should stop.

### Functions

#### `train_epoch(model, data_loader, optimizer, criterion)`
Executes a single training epoch.
- **Logic**: Handles gradient accumulation and memory monitoring.
- **Fallback**: Reduces batch size if OOM is detected.

#### `train_model(model, train_loader, val_loader)`
Trains the model with early stopping.
- **Output**: Saves the best model weights to `results/models/gcn_best.pt`.

#### `generate_predictions(model, test_loader)`
Generates predictions for the test set.
- **Output**: Returns a DataFrame with `[smiles, predicted_sasa, error]`.

---

## Module: `code/eval/metrics.py`

Implements evaluation metrics and statistical tests.

### Functions

#### `calculate_mae(y_true, y_pred)`
Calculates Mean Absolute Error.

#### `calculate_rmse(y_true, y_pred)`
Calculates Root Mean Square Error.

#### `calculate_r2(y_true, y_pred)`
Calculates R-squared coefficient.

#### `paired_ttest(errors_gcn, errors_baseline)`
Performs a paired t-test between two sets of errors.
- **Returns**: t-statistic and p-value.

#### `cohen_d(errors_gcn, errors_baseline)`
Calculates Cohen's d effect size.

#### `bonferroni_correction(p_values, n_tests)`
Applies Bonferroni correction for multiple comparisons.

#### `fdr_correction(p_values)`
Applies False Discovery Rate (FDR) correction.

---

## Module: `code/eval/sensitivity.py`

Performs sensitivity analysis on MAE thresholds.

### Functions

#### `load_predictions(path)`
Loads prediction data from Parquet files.

#### `calculate_success_rate(errors, threshold)`
Calculates the fraction of predictions with error < threshold.

#### `run_sensitivity_analysis_absolute(predictions)`
Runs the sensitivity analysis for absolute thresholds `[0.01, 0.05, 0.1]`.
- **Output**: Generates `data/processed/sensitivity_absolute.csv`.

#### `run_multiple_comparison_correction(results)`
Applies statistical correction (Bonferroni or FDR) to the sensitivity results.
- **Logic**: Uses Bonferroni if n <= 5, FDR otherwise.

#### `generate_reproducibility_report(sample_size)`
Generates a report detailing limitations and statistical power.

---

## Traceability to Functional Requirements

- **FR-001 (Data Ingestion)**: Implemented in `code/data/ingest.py` with streaming and checksumming.
- **FR-002 (Graph Generation)**: Implemented in `code/data/preprocess.py` (2D features) and `code/data_models/graph.py`.
- **FR-003 (3D Conformer & SASA)**: Implemented in `code/data/preprocess.py` (ETKDG, SASA).
- **FR-004 (Baseline Models)**: Implemented in `code/models/baseline.py` (2D and 3D baselines).
- **FR-005 (GCN Training)**: Implemented in `code/models/train.py` and `code/models/gcn.py`.
- **FR-006 (Sensitivity Thresholds)**: Implemented in `code/eval/sensitivity.py` with absolute thresholds.
- **FR-007 (Multiple Comparisons)**: Implemented in `code/eval/sensitivity.py` and `code/eval/metrics.py` (Bonferroni/FDR).