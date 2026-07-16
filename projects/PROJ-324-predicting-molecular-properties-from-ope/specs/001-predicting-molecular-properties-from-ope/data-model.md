# Data Model Specification

## Raw Data
- **Source**: HuggingFace datasets (ChEMBL, MoleculeNet).
- **Format**: Parquet or CSV.
- **Fields**:
 - `smiles`: String (canonical SMILES).
 - `logp`: Float (experimental logP).
 - `solubility`: Float (experimental solubility in mol/L).
 - `boiling_point`: Float (experimental boiling point in Kelvin).
 - `source`: String (dataset name).
 - `confidence`: Float (measurement confidence score).

## Processed Data
- **Format**: Parquet.
- **Fields**:
 - `molecule_id`: String (unique identifier).
 - `smiles`: String.
 - `logp`: Float.
 - `solubility`: Float.
 - `boiling_point`: Float.
 - `fingerprint_ecfp4`: Array[uint8].
 - `fingerprint_maccs`: Array[uint8].
 - `fingerprint_fp2`: Array[uint8].
 - `is_train`: Boolean.

## Derived Data
- **Format**: CSV.
- **Files**:
 - `baseline_predictions.csv`: `molecule_id`, `smiles`, `logp_exp`, `logp_pred`, `error`.
 - `data_quality_report.csv`: `molecule_id`, `missing_covariate`, `exclusion_reason`.
 - `shap_interactions.csv`: `bit_pair`, `interaction_strength`, `substructure_description`.
