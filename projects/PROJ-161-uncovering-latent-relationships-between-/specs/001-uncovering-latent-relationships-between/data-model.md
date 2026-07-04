# Data Model: Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance

## 1. Entities

### 1.1 AntibioticCompound
Represents a single drug entity.
- `inchi_key` (string): Primary key, canonicalized.
- `smiles` (string): Canonicalized SMILES.
- `source` (string): "chembl", "zinc15", "ncbi".
- `resistance_frequency` (float): Aggregated frequency from NCBI (0.0 to 1.0). **Definition**: `resistant_isolates / total_tested_isolates` for the compound.
- `observation_count` (int): Number of organism-strain observations used for aggregation (min 5).
- `resistance_label` (string): "High", "Low", "Unknown", or "Continuous". **Derivation**: Derived from quartiles if Hartigan's Dip Test passes, GMM clusters if Dip fails, or "Continuous" if GMM fails.
- `valid` (boolean): True if SMILES parsed and descriptors calculated.

### 1.2 MolecularDescriptorSet
Vector of properties for a compound.
- `compound_id` (string): FK to AntibioticCompound.
- `logP` (float): Partition coefficient.
- `TPSA` (float): Topological Polar Surface Area.
- `HBD` (int): Hydrogen Bond Donors.
- `HBA` (int): Hydrogen Bond Acceptors.
- `RotBonds` (int): Rotatable bonds.
- `MW` (float): Molecular Weight.
- `vif_score` (float): Variance Inflation Factor (only for descriptors passing VIF < 5).
- *(+ numerous other descriptors)*

### 1.3 ClusterGroup
Result of DBSCAN clustering.
- `cluster_id` (int): DBSCAN label (-1 for noise).
- `centroid_x` (float): UMAP X coordinate.
- `centroid_y` (float): UMAP Y coordinate.
- `size` (int): Number of compounds.
- `enrichment_p_value` (float): Fisher's exact test p-value (from label permutation).
- `enrichment_fdr` (float): BH-corrected p-value.
- `is_significant` (boolean): True if FDR < 0.05.

### 1.4 MergeMetrics
Output for SC-001.
- `total_requested` (int): Number of compounds requested.
- `successful_matches` (int): Number of compounds with valid InChIKey match.
- `merge_fraction` (float): Ratio of matches to requested.

### 1.5 RuntimeMetrics
Output for SC-004.
- `total_duration_seconds` (float): Total pipeline runtime.
- `status` (string): "success", "timeout", "error".

## 2. Data Flow

1. **Raw Input**:
   - `raw/chembl_descriptors.csv` (from HuggingFace)
   - `raw/ncbi_resistance.tsv` (from FTP)
2. **Processing**:
   - `data/processed/merged_compounds.parquet` (InChIKey join, aggregation)
   - `data/processed/descriptors_matrix.parquet` (NumPy array)
   - `data/processed/merge_metrics.json` (SC-001 output)
3. **Analysis**:
   - `data/processed/umap_embedding.parquet`
   - `data/processed/clustering_results.csv`
   - `data/processed/statistical_tests.csv`
4. **Output**:
   - `data/processed/final_ranking.csv` (Top descriptors by effect size)
   - `data/processed/runtime_metrics.json` (SC-004 output)
   - `data/figures/umap_plot.png`
   - `data/figures/distribution_check.png`

## 3. Constraints & Validation
- **InChIKey**: Must match regex `^[A-Z]{14}-[A-Z]{10}-[A-Z]$`.
- **Descriptors**: Must be numeric; NaNs allowed but flagged.
- **Resistance Label**: Derived from quartiles (Top [deferred] = High, Bottom [deferred] = Low) OR GMM OR Continuous.
- **Seeds**: All random seeds pinned to `42`.
- **Observation Count**: Must be >= 5 for inclusion.
- **VIF Threshold**: Descriptors with VIF >= 5 are excluded from univariate testing.