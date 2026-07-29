# Contract Tests Specification

## T011: Data Download Contract
- **Script**: `code/download_data.py`
- **Verification**:
 - File exists at `data/raw/experimental_barriers.csv`
 - File checksum matches expected Zenodo hash
 - CSV contains columns: `smiles`, `experimental_barrier`
 - No NaN values in `experimental_barrier`

## T012: Descriptor Generation Contract
- **Script**: `code/generate_descriptors.py`
- **Verification**:
 - Output file `data/processed/descriptors_semi.csv` exists
 - Contains exactly 50 rows (for test subset)
 - No NaN values in numerical columns
 - `homo` < `lumo` for all rows
 - `net_charge` sums correctly for known test molecules

## T018: Model Training Contract
- **Script**: `code/train_models.py`
- **Verification**:
 - Two Random Forest models trained
 - Models saved to `data/processed/model_outputs/`
 - 5-fold CV executed without error
 - Output metrics (MAE) are finite and positive

## T019: Evaluation Contract
- **Script**: `code/evaluate_models.py`
- **Verification**:
 - `evaluation.json` generated
 - `p_value` is finite
 - Threshold flags are boolean
 - Speedup ratio calculated correctly
