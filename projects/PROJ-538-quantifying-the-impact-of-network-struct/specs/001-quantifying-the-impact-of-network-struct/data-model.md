# Data Model: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## 1. Entity-Relationship Overview

The system processes three primary entities:
1.  **AtomicSnapshot**: Raw input data (positions, species, thermal conductivity).
2.  **DefectGraph**: Derived graph structure and computed topological metrics.
3.  **CorrelationResult**: Statistical outcomes of the analysis.
4.  **SensitivityResult**: Outcomes of the threshold sweep (SC-004).

## 2. Schema Definitions

### 2.1 AtomicSnapshot
Represents a single molecular dynamics configuration.
- **atomic_indices**: List[int] - Unique identifiers for atoms.
- **coordinates**: List[Tuple[float, float, float]] - (x, y, z) positions.
- **species**: List[str] - Element symbols (e.g., "Cu", "Ni").
- **thermal_conductivity**: float - Pre-calculated thermal conductivity (W/m·K) or synthetic proxy.
- **source_file**: str - Path to the original data file or "synthetic".
- **mode**: str - "real" or "synthetic".

### 2.2 DefectGraph
Represents the topological structure of the alloy's defects.
- **snapshot_id**: str - Reference to the source AtomicSnapshot.
- **num_nodes**: int - Total number of atoms.
- **num_edges**: int - Number of mismatched-species connections.
- **clustering_coefficient**: float - Average local clustering.
- **mean_degree**: float - Average node degree.
- **degree_variance**: float - Variance of the degree distribution.
- **percolation_threshold**: float | null - Estimated threshold (null if undefined).
- **is_disconnected**: bool - Flag indicating if the graph has multiple components.

### 2.3 CorrelationResult
Represents the statistical relationship between a metric and thermal conductivity.
- **metric_name**: str - Name of the topological metric (e.g., "clustering_coefficient").
- **correlation_coefficient**: float - Pearson or Spearman $r$/$\rho$.
- **p_value_raw**: float - Uncorrected p-value.
- **p_value_corrected**: float - Bonferroni-corrected p-value.
- **is_significant**: bool - True if $p_{corrected} < 0.05$.
- **sample_size**: int - Number of snapshots used ($N$).
- **power**: float - Post-hoc statistical power.
- **mode**: str - "real" or "synthetic".

### 2.4 SensitivityResult
Represents the outcome of the threshold sweep (SC-004).
- **threshold**: float - The p-value threshold used (e.g., 0.01, 0.05).
- **stable_rank_order**: bool - True if rank order of metrics remained stable.
- **max_magnitude_change**: float - Maximum change in correlation magnitude across thresholds.
- **conclusion_stable**: bool - True if the overall conclusion (significant/not) remained stable.

## 3. Data Flow

1.  **Ingest**: `AtomicSnapshot` -> (Voronoi + Species Check) -> `DefectGraph`
2.  **Analyze**: `DefectGraph` (metrics) + `AtomicSnapshot` (conductivity) -> `CorrelationResult`
3.  **Sensitivity**: `CorrelationResult` (across thresholds) -> `SensitivityResult`
4.  **Visualize**: `CorrelationResult` -> PNG Figures

## 4. Constraints & Validation Rules

- **Species Mismatch**: Edges MUST NOT exist between same-species atoms.
- **Thermal Conductivity**: Must be > 0.
- **Missing Data**: If `thermal_conductivity` is missing, the snapshot is excluded from correlation but logged.
- **NaN Handling**: Metrics that cannot be computed (e.g., $p_c$ on a single node) must be `null`/`NaN`, not 0 or infinity.
- **Mode Labeling**: All artifacts MUST be labeled as "real" or "synthetic" to prevent confusion.
- **Ensemble Independence**: Synthetic snapshots must be generated with unique seeds and thermalization steps to ensure statistical independence.
