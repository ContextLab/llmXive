# Data Model: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## Entity Definitions

### 1. Molecule
Represents a single chemical entity in the dataset.
- **`smiles`**: (string) Canonical SMILES string after standardization (salt removal, tautomerization).
- **`pce`**: (float) Experimental Power Conversion Efficiency in percentage (%).
- **`scaffold`**: (string) Bemis-Murcko scaffold string (used for splitting).
- **`molecular_weight`**: (float) Calculated molecular weight (used for confounding control).
- **`atom_count`**: (int) Total number of atoms (used for confounding control).
- **`graph_data`**: (dict) Pre-computed graph features:
  - `node_features`: (list of lists) Atomic features [atomic_num, hybridization, aromaticity, ...].
  - `edge_index`: (2, num_edges) Tensor of edge connections.
  - `edge_features`: (list of lists) Bond features [bond_type, aromaticity, ...].

### 2. ModelArtifact
Represents a trained model instance.
- **`model_type`**: (string) "GCN" or "RandomForest".
- **`fold_id`**: (int) Cross-validation fold index (0-4).
- **`metrics`**: (dict) Performance metrics:
  - `mae`: (float) Mean Absolute Error.
  - `rmse`: (float) Root Mean Square Error.
  - `r2`: (float) Coefficient of Determination.
- **`weights_path`**: (string) Path to saved model weights.

### 3. Motif
Represents a recurring substructure identified as predictive.
- **`subgraph_smiles`**: (string) SMILES of the substructure.
- **`frequency`**: (int) Number of times this motif appeared in high-PCE predictions.
- **`importance_score`**: (float) Average Integrated Gradient/GNNExplainer score for this motif.
- **`description`**: (string) Textual description (e.g., "Donor-π-Acceptor").
- **`validation_pce_diff`**: (float) Difference in average PCE between molecules with/without the motif (counterfactual check).

## Data Flow

1. **Raw Input**: `DSSC-Final-Datasets.jsonl` (SMILES, PCE) or `DSSC2024.parquet`.
2. **Preprocessed**: `data/processed/graphs.pkl` (Molecule entities with graph features, MW, atom count).
3. **Model Output**: `data/outputs/metrics.json` (ModelArtifact entities).
4. **Interpretation**: `data/outputs/motifs.csv` (Motif entities with validation scores).

## Constraints

- **PCE Range**: Must be > 0 and ≤ 30. Entries outside this range are flagged for manual review.
- **SMILES Validity**: Must be parsable by RDKit. Invalid SMILES are excluded.
- **Scaffold Uniqueness**: No scaffold in test fold may exist in training fold (unless fallback to stratified split is triggered).
- **Confounding Control**: Molecular Weight and Atom Count must be computed and stored for all molecules.