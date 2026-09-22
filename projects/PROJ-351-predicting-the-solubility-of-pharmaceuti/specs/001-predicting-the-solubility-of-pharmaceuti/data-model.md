# Data Model: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## 1. Entity Definitions

### 1.1 Molecule
Represents a single chemical compound.
- `smiles` (string): Canonical SMILES representation.
- `logS` (float): Measured aqueous solubility in mol/L (log scale).
- `graph` (RDKit Mol): Preprocessed molecular graph object.
- `features` (Tensor): Node and edge feature tensors for GNN input.
- `fingerprints` (ndarray): Morgan fingerprint bit vector (2048 bits) for RF.
- `is_valid` (bool): Flag indicating if the SMILES passed RDKit validation.

### 1.2 DatasetSplit
Represents a partitioned dataset for training, validation, and testing.
- `train_indices` (list[int]): Indices of molecules in the training set.
- `val_indices` (list[int]): Indices of molecules in the validation set.
- `test_indices` (list[int]): Indices of molecules in the test set.
- `logS_distribution` (dict): Statistics of logS in each split (mean, std, min, max).

### 1.3 Model
Represents a trained predictive model.
- `type` (string): "RandomForest" or "MPNN".
- `metrics` (dict): Performance metrics (RMSE, R², p-value, power).
- `weights_path` (string): Path to the saved model file.
- `config` (dict): Hyperparameters used for training.
- `fold_metrics` (list[dict]): Array of 5 objects, one per Outer Loop fold, containing `fold_id`, `rmse`, and `r_squared`.

### 1.4 PredictionResult
Represents the output of a model on a test set.
- `molecule_id` (int): Index of the molecule.
- `true_logS` (float): Actual logS value.
- `pred_logS` (float): Predicted logS value.
- `absolute_error` (float): |true - pred|.

## 2. Data Flow

1. **Raw Data**: `data/raw/delaney-processed.csv`
   - Source: S3/HuggingFace.
   - Format: CSV.
   - Action: Download, checksum, validate columns.

2. **Cleaned Data**: `data/processed/cleaned_molecules.pkl`
   - Action: Filter invalid SMILES, exclude NaN logS.
   - Output: List of `Molecule` objects.

3. **Graphs**: `data/processed/graphs.pkl`
   - Action: Convert valid SMILES to RDKit graphs, extract features.
   - Output: List of `Molecule` objects with `graph` and `features`.

4. **Splits**: `data/processed/splits.json`
   - Action: **Stratified Split** (10 bins) on `logS` to generate 5-fold indices (Outer Loop).
   - Output: `DatasetSplit` object.

5. **Models**: `artifacts/rf_model.pkl`, `artifacts/gnn_model.pt`
   - Action: Train RF (Nested CV) and MPNN (Nested CV).
   - Output: Saved model weights and config.

6. **Results**: `artifacts/results.json`
   - Action: Evaluate on Outer Loop test sets, perform Nadeau's t-test, power analysis.
   - Output: `PredictionResult` list and summary metrics.

## 3. Schema Definitions (Contracts)

The following schemas define the structure of key data artifacts.

### 3.1 Dataset Schema (Input)
```yaml
# contracts/dataset_schema.yaml
type: object
properties:
  smiles:
    type: string
    pattern: "^[A-Za-z0-9@#$%&*\\-+=\\[\\]{}<>~!]+$"
  measured log solubility in mols per litre:
    type: number
    minimum: -10.0
    maximum: 10.0
  Compound ID:
    type: string
required:
  - smiles
  - measured log solubility in mols per litre
```

### 3.2 Prediction Schema (Output)
```yaml
# contracts/prediction_schema.yaml
type: object
properties:
  molecule_id:
    type: integer
  true_logS:
    type: number
  pred_logS:
    type: number
  absolute_error:
    type: number
    minimum: 0.0
required:
  - molecule_id
  - true_logS
  - pred_logS
  - absolute_error
```

### 3.3 Metrics Summary Schema
```yaml
# contracts/metrics_summary_schema.yaml
type: object
properties:
  model_type:
    type: string
    enum: ["RandomForest", "MPNN"]
  rmse:
    type: number
  r_squared:
    type: number
  p_value:
    type: number
    minimum: 0.0
    maximum: 1.0
  statistical_power:
    type: number
    minimum: 0.0
    maximum: 1.0
  fold_metrics:
    type: array
    items:
      type: object
      properties:
        fold_id:
          type: integer
        rmse:
          type: number
        r_squared:
          type: number
required:
  - model_type
  - rmse
  - r_squared
  - p_value
  - statistical_power
```