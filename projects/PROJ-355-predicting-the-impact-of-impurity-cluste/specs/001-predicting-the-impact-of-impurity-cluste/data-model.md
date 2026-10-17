# Data Model: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview
The pipeline transforms raw bulk structures into a training dataset that couples interface‑specific clustering descriptors with segregation‑energy targets. All entities are versioned, checksummed, and stored as immutable CSV/JSON files.

## Entity Definitions

| Entity | Fields | Description |
|--------|--------|-------------|
| **BulkConfiguration** | `id` (str), `formula` (str), `lattice` (list[float]), `atoms` (list[dict]), `source_url` (str), `source_type` (enum["OQMD","MaterialsProject"]) | Raw bulk crystal from OQMD or the verified MP mirror. |
| **GrainBoundaryStructure** | `id` (str), `bulk_id` (str), `boundary_plane` (str), `misorientation_angle` (float), `supercell_atoms` (list[dict]), `interface_mask` (list[bool]) | GB supercell with impurity atoms placed at the interface. |
| **ClusteringDescriptor** | `gb_id` (str), `impurity_species` (str), `descriptor_type` (enum["rdf_peak","pair_correlation","voronoi_count"]), `value` (float), `interface_only` (bool) | Numeric descriptor computed **only** in the interface region. |
| **Covariate** | `gb_id` (str), `local_lattice_strain` (float), `atomic_radius` (float), `electronegativity` (float) | Additional predictors to control for confounding. |
| **SegregationEnergy** | `gb_id` (str), `impurity_species` (str), `energy_eV` (float), `potential_used` (str), `simulation_status` (enum["SUCCESS","FAILED","RETRY_EXHAUSTED"]), `simulation_time_s` (float) | Leave‑One‑Out segregation energy from empirical‑potential simulation. |
| **TrainingSample** | `sample_id` (str), `features` (list[float]), `target` (float), `alloy_system` (str), `vif_scores` (object), `descriptive_framing` (str) | Row fed to the regression model. |

## Data Flow Diagram
```mermaid
graph TD
    A[OQMD/MP Bulk Files] -->|download.py| B[Raw BulkConfiguration CSV]
    B -->|gb_builder.py| C[GrainBoundaryStructure JSON]
    C -->|descriptors.py| D[ClusteringDescriptor CSV]
    C -->|simulate_energy.py| E[SegregationEnergy CSV]
    D & E & Covariate CSV -->|train_model.py| F[TrainingSample CSV]
    F -->|metrics.json & sensitivity.json| G[Results]
```

## Hygiene & Provenance
- **Checksums**: SHA‑256 recorded in `data/metadata.yaml` for every raw and processed file.
- **Immutability**: Raw files never overwritten; each transformation writes a new file with a timestamped name.
- **Metadata**: `data/metadata.yaml` captures source URLs, potential version, random seeds, and code hash.
- **Missing Data Handling**: Samples lacking a segregation‑energy label or with zero impurity atoms are excluded and logged (FR‑007 edge case).

## Validation Constraints (directly map to FR/SC)
- **FR‑001**: `download.py` enforces ≤ 3 retries; logs `[DATA_UNAVAILABLE]` on permanent failure.
- **FR‑002**: `descriptors.py` outputs three descriptor types per impurity, computed only inside the interface mask.
- **FR‑003**: `simulate_energy.py` produces segregation‑energy entries; optional DFT validation is performed only as a sanity check.
- **FR‑004**: `train_model.py` computes R², RMSE, and coefficient p‑values for each CV fold.
- **FR‑005**: Multiple‑comparison correction applied inside `train_model.py`.
- **FR‑006**: Sensitivity sweep over three λ values (25th, 50th, 75th percentiles) reports RMSE variance and R² stability.
- **FR‑007**: VIF computed on the three raw descriptors before modeling; if any VIF ≥ 10, `descriptive_framing` is populated.
- **SC‑001–SC‑005**: All are recorded in `results/metrics.json` and `results/sensitivity.json` per the output schema.

## Dataset Output
The assembled training set is written to `data/processed/training_set.csv` and validated against `contracts/dataset.schema.yaml`. The file contains the fields listed in the schema (see that contract).
