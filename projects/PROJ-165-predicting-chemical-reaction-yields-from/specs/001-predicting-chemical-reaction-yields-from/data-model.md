# Data Model: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## 1. Entity Definitions

### ReactionSample
Represents a single chemical reaction instance.
- `id`: `str` (UUID)
- `reaction_smiles`: `str` (Canonical SMILES)
- `yield_percent`: `float` (0.0 - 100.0)
- `ir_spectrum`: `List[float]` (Resampled to 400-4000 cm⁻¹, length=3601)
- `nmr_spectrum`: `List[float]` (Resampled to 0-10 ppm, length=1001)
- `rfp`: `List[int]` (ECFP4 fingerprint, length=2048)
- `reaction_template_id`: `str` (Hash of reaction center)
- `solvent_id`: `int` (Encoded category)
- `catalyst_id`: `int` (Encoded category)
- `temperature_k`: `float`
- `source`: `str` (e.g., "USPTO", "DFT_Simulated")

### SpectralGrid
Defines the standardized domain.
- `type`: `str` ("IR", "NMR")
- `min_value`: `float`
- `max_value`: `float`
- `num_bins`: `int`

### ModelCheckpoint
- `epoch`: `int`
- `validation_rmse`: `float`
- `weights_path`: `str`
- `config_hash`: `str`

## 2. Data Flow Diagram

1.  **Ingestion**: Raw files (Parquet/CSV) -> `data/raw/` (Checksummed).
2.  **Preprocessing**:
    - Extract SMILES, Yield, Conditions.
    - Generate/Load Spectra.
    - Resample & Normalize.
    - Extract Templates -> Split (Train/Val/Test).
    - Output: `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
3.  **Training**:
    - Load `train.parquet` -> `torch.utils.data.DataLoader`.
    - Model Forward -> Loss (MSE) -> Backward -> Update.
    - Log metrics -> `data/artifacts/training_log.json`.
4.  **Evaluation**:
    - Load `test.parquet` + Model -> Predictions.
    - Compute Metrics (RMSE, MAE, R²).
    - Run Permutation Test.
    - Generate Heatmaps.
    - Output: `data/artifacts/evaluation_report.json`, `figures/`.

## 3. Schema Constraints

- **Yield**: Must be in range [0, 100].
- **Spectra**: Must have fixed length (grid size).
- **Templates**: Must be unique per sample; no overlap across splits.
- **Missing Data**: Samples with missing spectra or yield are dropped (or masked if masking logic implemented).

## 4. File Formats

- **Raw Data**: Parquet (USPTO), CSV (NMR).
- **Processed Data**: Parquet (compressed).
- **Logs/Reports**: JSON.
- **Models**: `.pt` (PyTorch).
- **Config**: YAML.
