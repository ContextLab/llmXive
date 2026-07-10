# Data Model: Predicting Molecular Excitation Wavelengths

## 1. Entities

### Molecule
Represents a single chemical entity.
- **smiles**: String (Canonical SMILES).
- **mol_id**: String (Unique identifier, hash of SMILES).
- **lambda_max**: Float (Experimental or computed $\lambda_{max}$ in nm).
- **scaffold_id**: String (Bemis-Murcko scaffold identifier).
- **is_valid**: Boolean (RDKit parsing status).

### Split
Represents the data partitioning strategy.
- **split_name**: String (`train`, `val`, `test`).
- **molecule_ids**: List of Strings.

### Prediction
Represents a model output.
- **mol_id**: String.
- **predicted_lambda**: Float.
- **actual_lambda**: Float.
- **error**: Float (Absolute error).
- **attribution_weights**: Dict (Atom/Bond level weights from GNNExplainer).

## 2. Data Flow

1. **Raw Ingestion**: `data/raw/uvvisml.csv` -> `code/ingest.py` -> `data/processed/cleaned.csv`.
2. **Splitting**: `cleaned.csv` -> `code/split.py` -> `data/processed/train.csv`, `val.csv`, `test.csv`.
3. **Training**: `train.csv` + `val.csv` -> `code/train.py` -> `artifacts/model.pt`.
4. **Evaluation**: `test.csv` + `model.pt` -> `code/evaluate.py` -> `artifacts/results.csv`.
5. **Attribution**: `test.csv` + `model.pt` -> `code/explain.py` -> `artifacts/attribution.json`.

## 3. Schema Definitions

The following schemas define the contract for data interchange.
