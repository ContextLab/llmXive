# Data Model: Predicting Molecular Properties from Topological Data Analysis

## Entities & Relationships

### Molecule
- **Identifier**: `smiles` (string, canonicalized)
- **Properties**: `molecular_weight` (float), `logP` (float, optional), `solubility` (float, optional), `boiling_point` (float, optional)
- **Graph**: Constructed from SMILES; nodes=atoms, edges=bonds.
- **Status**: `valid` (bool), `excluded_reason` (string, if invalid)

### TopologicalDescriptor
- **Source**: `molecule.smiles`
- **Filtration**: `shortest_path_distance`
- **Vectorization**: `persistence_image`
- **Dimensions**: `grid_size` (int, e.g., 10, 20, 30), `kernel_bandwidth` (float)
- **Output**: `feature_vector` (array of floats), `betti_curves` (optional)

### ModelPerformance
- **Configuration**: `feature_set` (enum: "traditional", "topological", "combined"), `model_type` (enum: "linear_l2", "rf")
- **Metrics**: `r2_mean`, `r2_std`, `rmse_mean`, `rmse_std`
- **Validation**: `fold_scores` (array), `scaffold_split_seed` (int)
- **Comparison**: `p_value`, `bonferroni_adjusted_p`, `significant` (bool)

## Data Flow

1.  **Ingestion**: Raw CSV/Parquet → `Molecule` table (validated, filtered).
2.  **TDA Computation**: `Molecule` → `TopologicalDescriptor` (feature vectors).
3.  **Feature Engineering**: `Molecule` + `TopologicalDescriptor` → `CombinedFeatureMatrix`.
4.  **Modeling**: `CombinedFeatureMatrix` + `Target` → `ModelPerformance` (per fold).
5.  **Diagnostics**: `CombinedFeatureMatrix` → `VIF`, `MutualInformation` → `DiagnosticsReport`.

## Storage Schema

-   **Raw Data**: `data/raw/<dataset_name>.csv` or `.parquet`
-   **Processed Features**: `data/processed/<molecule_id>_features.csv` (or aggregated `feature_matrix.csv`)
-   **Model Outputs**: `reports/metrics/<property>_<model>.json`
-   **Diagnostics**: `reports/diagnostics/vif_report.json`, `reports/diagnostics/mi_report.json`
