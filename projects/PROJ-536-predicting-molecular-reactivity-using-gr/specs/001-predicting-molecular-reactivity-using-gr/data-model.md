# Data Model: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

## Entity Definitions

### ReactionRecord
Represents a single chemical reaction instance.
- **id**: Unique identifier (string).
- **reactants_smiles**: List of SMILES strings for reactants.
- **product_smiles**: SMILES string for the product.
- **yield**: Float (0.0 to 100.0). Target variable.
- **reaction_class**: String (e.g., "Acylation", "Suzuki"). Used for reference only (not for splitting).
- **scaffold**: String. The MurckoScaffold of the product molecule, used for grouping/splitting.
- **parsed**: Boolean. True if SMILES were successfully converted to graphs.
- **error_log**: String. Reason for parsing failure (if `parsed` is False).

### MolecularGraph
A graph data structure derived from a SMILES string.
- **nodes**: List of Node objects.
  - **atomic_number**: Integer.
  - **charge**: Integer.
  - **hybridization**: Enum (SP, SP2, SP3, etc.).
  - **is_aromatic**: Boolean.
- **edges**: List of Edge objects.
  - **bond_type**: Enum (SINGLE, DOUBLE, TRIPLE, AROMATIC).
  - **is_conjugated**: Boolean.
- **is_valid**: Boolean. Result of RDKit valence/aromaticity checks.

### ModelEvaluation
Result set for a specific model on a specific split (or fold).
- **model_type**: Enum (GNN, RF, LR).
- **split_name**: String (train, val, test, or "fold-{N}").
- **fold_id**: Integer (if using CV).
- **r2**: Float.
- **r2_ci_low**: Float. (Lower bound of 95% CI for R², if aggregated).
- **r2_ci_high**: Float. (Upper bound of 95% CI for R², if aggregated).
- **mae**: Float.
- **rmse**: Float.
- **loss_history**: List of Float (per epoch).
- **p_value**: Float (if statistical test performed).
- **comparison_baseline**: String (e.g., "RF").
- **r2_delta**: Float. (R²_GNN - R²_Baseline).
- **r2_delta_ci_low**: Float. (Lower bound of 95% CI for R² delta).
- **r2_delta_ci_high**: Float. (Upper bound of 95% CI for R² delta).
- **significance_assessment**: String. (e.g., "Practically Significant", "Statistically Significant, but effect size uncertain", "No Statistical Significance").

### PredictionInterval
Uncertainty estimate for a single prediction.
- **reaction_id**: String.
- **predicted_yield**: Float.
- **lower_bound**: Float.
- **upper_bound**: Float.
- **actual_yield**: Float (for evaluation).
- **is_covered**: Boolean. True if `lower_bound <= actual_yield <= upper_bound`.

### SubgraphPattern
Motif identified by GNNExplainer.
- **pattern_id**: String.
- **nodes**: List of node indices in the original graph.
- **edges**: List of edge indices.
- **importance_score**: Float.
- **frequency**: Integer. How often this pattern appears in high-importance regions.
- **interpretation_warning**: String. **Mandatory**: "These patterns are associational and may reflect dataset bias; they are not proven causal drivers."

## Data Flow

1.  **Raw Input**: Parquet file (USPTO) -> `download.py`
2.  **Validation**: Verify `yield` and `smiles` columns exist.
3.  **Parsing**: Parquet -> `parse.py` -> `ReactionRecord` (with graph conversion).
4.  **Scaffolding**: Compute MurckoScaffold for each record.
5.  **Splitting**: `ReactionRecord` -> Grouped by Scaffold -> Train/Val/Test splits.
6.  **Feature Extraction**:
    - GNN: `MolecularGraph` tensors.
    - RF/LR: `MolecularGraph` -> `numpy` arrays (fingerprints/descriptors).
7.  **Training**: `train.py` (5-Fold CV) -> `ModelEvaluation` (per fold).
8.  **Aggregation**: Compute mean/std, statistical tests, and CIs -> `ModelEvaluation` (aggregated).
9.  **Inference**: `evaluate.py` -> `ModelEvaluation` (metrics) + `PredictionInterval`.
10. **Explanation**: `explainers.py` -> `SubgraphPattern` (with warning).

## Storage Format

- **Raw Data**: Parquet (immutable).
- **Processed Data**: HDF5 or Pickle (for graph tensors), CSV (for descriptors).
- **Models**: PyTorch `.pt` files.
- **Results**: JSON (metrics), CSV (intervals).
