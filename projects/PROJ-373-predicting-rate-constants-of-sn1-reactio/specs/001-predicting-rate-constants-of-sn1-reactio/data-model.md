# Data Model: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## Entity Definitions

### Molecule
- **SMILES**: string (canonicalized)
- **Substrate Class**: string (secondary, tertiary) — *must be explicit in source*
- **Descriptors**: dict (Gasteiger charges, topological indices)
- **Exclusion Reason**: string (if invalid)

### ReactionRate
- **Rate Constant**: float (s⁻¹ or M⁻¹s⁻¹, normalized to s⁻¹)
- **Temperature**: float (K)
- **Solvent**: string
- **Source ID**: string (dataset ID)
- **Exclusion Reason**: string (if invalid)

### ModelConfiguration
- **Hyperparameters**: dict (learning_rate, hidden_dim, dropout)
- **Performance Metrics**: dict (R², MAE)
- **Seed**: int (42)

### CollinearPair
- **Descriptor A**: string
- **Descriptor B**: string
- **VIF Score**: float
- **Flag Reason**: string

### Descriptor
- **Name**: string
- **Value**: float
- **Type**: string (topological, electronic)
- **Source Method**: string (Gasteiger, RDKit)

## Data Flow

1. **Ingestion**: Raw JSONL/Parquet → Validate columns → Exclude if missing metadata → Clean (remove NaN, invalid SMILES) → Output `cleaned.csv`.
2. **Descriptor Computation**: `cleaned.csv` → RDKit → Compute Gasteiger/topological descriptors → Output `descriptors.csv`.
3. **Splitting**: `descriptors.csv` → Stratified by substrate class → Train/Val/Test (70/15/15) → Output `split_*.csv`.
4. **Training**: `train.csv` → MPNN (Nested CV) → Output `model.pt`, `metrics.json`.
5. **Evaluation**: `test.csv` → Predictions → Bootstrap comparison → Output `comparison_report.json`.
6. **Interpretability**: Model + `test.csv` → SHAP → Sensitivity → Perturbation → VIF → Output `shap_report.md`, `sensitivity_report.md`, `perturbation_report.md`, `vif_report.json`.
7. **Consistency Check**: Re-run with 5 seeds → Output `shap_consistency_report.md`.

## Constraints

- No in-place modification of raw data.
- All derived files checksummed.
- Deterministic seeding enforced.
- No causal language in outputs.
- Unit normalization: All rate constants converted to s⁻¹.