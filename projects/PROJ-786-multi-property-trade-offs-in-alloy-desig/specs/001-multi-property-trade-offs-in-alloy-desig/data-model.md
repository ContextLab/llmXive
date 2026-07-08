# Data Model: Multi-Property Trade-Offs in Alloy Design

## 1. Entity Definitions

### AlloyEntry
Represents a single processed alloy data point.
*   `id`: Unique identifier (string).
*   `composition`: Dictionary `{element: fraction}`.
*   `bulk_modulus`: Float (GPa) - **Primary Target** (DFT-derived).
*   `shear_modulus`: Float (GPa) - **Primary Target** (DFT-derived).
*   `yield_strength`: Float (MPa) - **Optional** (Experimental, likely null).
*   `elongation`: Float (%) - **Optional** (Experimental, likely null).
*   `feature_vector`: List of floats (encoded features).
*   `system`: String (e.g., "Fe-Cr").
*   `source`: String (Dataset URL).

### ParetoFrontier
A set of non-dominated points.
*   `points`: List of `SyntheticAlloy`.
*   `dominance_ratio`: Float (Percentage of empirical points dominated).

### DecoupledRegion
A cluster with low correlation (high deviation from global trend).
*   `cluster_id`: Integer.
*   `global_correlation`: Float (Global Pearson r).
*   `local_correlation`: Float (Cluster Pearson r).
*   `deviation_score`: Float ($|r_{global} - r_{local}|$).
*   `point_count`: Integer.
*   `uncertainty_variance`: Float.
*   `is_significant`: Boolean (based on permutation test p-value).

## 2. Data Flow

1.  **Raw Input**: OQMD CSV/Parquet -> `data/raw/`.
2.  **Ingestion**: Filter missing values (bulk/shear) -> `data/processed/filtered.csv`.
3.  **Encoding**: Add periodic descriptors -> `data/processed/encoded.csv`.
4.  **Model**: Train GBM -> `data/processed/models/`.
5.  **Optimization**: Generate Pareto -> `data/processed/results/pareto_frontier.csv`.
6.  **Analysis**: Cluster & Deviation -> `data/processed/results/decoupled_regions.json`.

## 3. Schema Constraints

*   **Compositional Sum**: Sum of elemental fractions must be 1.0 (±0.001).
*   **Physical Bounds**: Bulk/Shear Moduli must be > 0.
*   **Feature Vector**: Fixed length based on the periodic table subset used.
*   **Proxy Mode**: If `yield_strength` and `elongation` are null, `bulk_modulus` and `shear_modulus` MUST be present.