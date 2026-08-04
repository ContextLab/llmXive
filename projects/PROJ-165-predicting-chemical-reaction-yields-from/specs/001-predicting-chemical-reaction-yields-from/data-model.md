# Data Model: Predicting Chemical Reaction Yields from Spectroscopic Data

## 1. Entity Definitions

### 1.1 ReactionSample
Represents a single chemical reaction instance with all associated features.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `reaction_smiles` | String | Canonical SMILES of the reaction (e.g., `C+C>>C`). | DFT |
| `yield_percent` | Float | Reaction yield (0.0 - 100.0). | DFT |
| `ir_spectrum` | Array[Float] | Resampled IR spectrum (e.g., 400-4000 cm⁻¹, 200 bins). | DFT |
| `nmr_spectrum` | Array[Float] | Resampled NMR spectrum (0-10 ppm, 200 bins). | DFT |
| `fingerprint` | Array[Int] | ECFP4 fingerprint (1024 bits). | RDKit |
| `reaction_template_id` | String | Hash of the reaction center substructure (for splitting). | Derived |
| `solvent_id` | Int | Encoded solvent ID (or -1 if missing). | Derived |
| `catalyst_id` | Int | Encoded catalyst ID (or -1 if missing). | Derived |
| `temperature_k` | Float | Temperature in Kelvin. | Derived |
| `is_simulated` | Bool | Flag indicating if data is from DFT simulation. | Metadata |

### 1.2 SpectralGrid
Defines the standardized domain for spectral inputs.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `type` | Enum | `IR`, `Raman`, `NMR`. |
| `min_value` | Float | Minimum wavenumber/shift (e.g., 400.0). |
| `max_value` | Float | Maximum wavenumber/shift (e.g., 4000.0). |
| `num_bins` | Int | Number of resampled points (e.g., 200). |
| `step_size` | Float | Derived step size. |

### 1.3 ModelCheckpoint
Represents a saved state of the trained model.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `epoch` | Int | Training epoch number. |
| `validation_rmse` | Float | RMSE on validation set. |
| `weights_path` | String | Relative path to `.pt` file. |
| `config_hash` | String | SHA256 of model config. |
| `seed` | Int | Random seed used. |

## 2. Data Flow & Transformations

1.  **Raw Ingestion**:
    *   Input: Parquet files from Hugging Face.
    *   Transformation: Extract SMILES, compute fingerprints (RDKit), parse conditions.
    *   Output: `data/raw/intermediate.parquet`.

2.  **Spectral Preprocessing**:
    *   Input: Raw spectral arrays (variable length).
    *   Transformation: Resample to `SpectralGrid`, normalize (unit variance), handle missing channels (masking).
    *   Output: `data/processed/spectra_resampled.parquet`.

3.  **Splitting (Leakage Prevention)**:
    *   Input: `ReactionSample` list.
    *   Transformation: Group by `reaction_template_id`. Split groups 70/15/15.
    *   Output: `data/processed/train.parquet`, `data/processed/val.parquet`, `data/processed/test.parquet`.
    *   Artifact: `data/artifacts/leakage_report.json` (MD5 hashes of templates in each set).

4.  **Model Input**:
    *   Input: Preprocessed samples.
    *   Transformation: Batch creation, tensor conversion.
    *   Output: PyTorch `DataLoader` batches.

5.  **Evaluation Output**:
    *   Input: Predictions vs. Ground Truth.
    *   Transformation: Compute RMSE, MAE, R², Attention Weights.
    *   Output: `data/artifacts/metrics.json`, `data/artifacts/attention_heatmaps.png`.

## 3. Data Constraints

*   **Yield Range**: Clamped to [0, 100].
*   **Spectral Normalization**: All spectra normalized to mean=0, std=1 *per channel* across the training set.
*   **Template Uniqueness**: No `reaction_template_id` appears in >1 split.
*   **Missing Data**: If `ir_spectrum` or `nmr_spectrum` is missing, the array is filled with zeros and a `mask` vector is set to 0 for that channel.

## 4. Artifact Definitions

### 4.1 Integrity Report (`data/artifacts/integrity_report.json`)
*   **Purpose**: FR-015 Simulated Data Integrity Check.
*   **Content**: R² score of MLP predicting spectrum from fingerprint, threshold (0.95), and pass/fail status.

### 4.2 VIF Report (`data/artifacts/vif_report.json`)
*   **Purpose**: FR-016 Collinearity Check.
*   **Content**: VIF scores between spectral and fingerprint inputs, and a flag if VIF > 5.

### 4.3 Sensitivity Analysis (`data/artifacts/sensitivity_analysis.json`)
*   **Purpose**: FR-009 Sensitivity Analysis.
*   **Content**: Results for thresholds [90, 95, 99] (e.g., peak locations, stability metrics).

### 4.4 Simulated Validation Report (`data/artifacts/simulated_validation_report.json`)
*   **Purpose**: FR-010 Simulated Validation Report.
*   **Content**: Documentation of reliance on simulated data, inability to validate against experimental reality, and limitations.

### 4.5 Limitation Note (`data/artifacts/limitation_note.md`)
*   **Purpose**: FR-010 Clear Limitation Note.
*   **Content**: Markdown file detailing the data mismatch and the pivot to simulated data.

### 4.6 Power Analysis (`data/artifacts/power_analysis.json`)
*   **Purpose**: Statistical Power & Effective Sample Size.
*   **Content**: N_templates, power estimate, and test validity flag (valid/underpowered).

### 4.7 Non-Linear Check (`data/artifacts/nonlinear_check.json`)
*   **Purpose**: Scientific Soundness (Non-Linear Check).
*   **Content**: RF R² score (threshold 0.8) and flag if VIF is insufficient.