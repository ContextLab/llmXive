# Data Model: Predicting Molecular Stability from Spectroscopic Data

## Entity Definitions

### ReactionSample
Represents a single chemical reaction instance after preprocessing.
- `reaction_smiles`: str (Canonical SMILES of the reaction)
- `yield_percent`: float (0.0 to 100.0, or **normalized DFT total energy proxy**)
- `ir_spectrum`: list[float] (Resampled array, length = num_bins_IR)
- `nmr_spectrum`: list[float] (Resampled array, length = num_bins_NMR, or null if missing)
- `rfp`: list[int] (ECFP4 fingerprint vector, length = 2048)
- `scaffold_id`: str (Hash of the Bemis-Murcko scaffold)
- `solvent_id`: int (Encoded categorical ID)
- `catalyst_id`: int (Encoded categorical ID)
- `temperature_k`: float (Absolute temperature)
- `source_dataset`: str (e.g., "DFT")

### SpectralGrid
Defines the standardized domain for spectral data.
- `type`: str ("IR", "Raman", "NMR")
- `min_value`: float (e.g., 400.0 for IR)
- `max_value`: float (e.g., 4000.0 for IR)
- `num_bins`: int (e.g., 1000)

### ModelCheckpoint
Represents a saved state of the trained model.
- `epoch`: int
- `validation_rmse`: float
- `weights_path`: str (Relative path to .pt file)
- `config_hash`: str (SHA-256 of the training config)

### EvaluationResult
Stores the output of the evaluation phase.
- `model_name`: str (e.g., "attention", "fingerprint_baseline")
- `rmse`: float
- `mae`: float
- `r2`: float
- `p_value`: float (from paired t-test vs best baseline)
- `attention_map`: list[float] (Averaged attention weights over spectral axis)

### AnalysisTrace
Links every statistic/figure to its source data and code.
- `statistic_id`: str (Unique ID for the statistic)
- `data_row_ids`: list[str] (List of row IDs from the processed dataset)
- `code_block_hash`: str (SHA-256 hash of the specific code block/script that generated the result)
- `artifact_path`: str (Path to the generated figure or metric file)
- `description`: str (Human-readable description of the statistic)

## Data Flow

1.  **Ingestion**: Raw data (DFT) is downloaded and stored in `data/raw/`.
2.  **Preprocessing**:
    - SMILES are parsed to extract scaffolds.
    - Spectra are resampled to `SpectralGrid`.
    - Conditions are one-hot or integer encoded.
    - Data is split into Train/Val/Test based on `scaffold_id` (zero overlap).
    - Output: `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
3.  **Training**:
    - Model loads `train.parquet`.
    - Trains for max 10 epochs.
    - Saves `ModelCheckpoint` to `data/artifacts/`.
4.  **Evaluation**:
    - Model and baselines are evaluated on `test.parquet`.
    - Attention maps are generated.
    - **AnalysisTrace** entries are created for every metric and figure.
    - Output: `data/artifacts/metrics.json`, `data/artifacts/attention_heatmap.png`, `data/artifacts/trace_log.json`.

## Constraints & Validation

- **Yield Range**: `yield_percent` must be between 0.0 and 100.0. If a proxy (DFT Energy) is used, the range must be normalized to this scale.
- **Spectral Length**: All `ir_spectrum` and `nmr_spectrum` arrays must have length equal to `num_bins` defined in `SpectralGrid`.
- **Scaffold Uniqueness**: The set of `scaffold_id` in `train` must be disjoint from `test` and `val`.
- **Missing Data**: If `nmr_spectrum` is missing, it is replaced with a zero vector and a mask flag is set (if the model supports masking).
- **SSoT Linkage**: Every statistic reported in the paper must have a corresponding `AnalysisTrace` entry. The `code_block_hash` must match the hash of the specific script/function used to generate the result.

## Linkage Mechanism (Principle IV)

To satisfy Principle IV (Single Source of Truth):
1.  The `src/utils/trace_logger.py` module is used to generate `AnalysisTrace` entries.
2.  Every time a statistic is calculated (e.g., RMSE), the logger records the `data_row_ids` and the `code_block_hash` of the function that calculated it.
3.  The `trace_log.json` file serves as the master index linking all figures and statistics to their source.
