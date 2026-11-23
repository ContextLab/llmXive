# Data Model Specification

## Entities

### SimulationRun
Represents a single simulation execution.

**Fields**:
- `run_id`: Unique identifier (UUID)
- `timestamp`: ISO 8601 datetime
- `matrix_size`: Integer $N$
- `seed`: Random seed value
- `perturbation_config`: Reference to PerturbationConfig
- `eigenvalues`: List of top 10 eigenvalues (sorted descending)
- `outlier_detected`: Boolean
- `raw_data_path`: Path to saved matrix instance
- `checksum`: SHA-256 hash of raw data

### PerturbationConfig
Defines the perturbation applied to the Wigner matrix.

**Fields**:
- `rank`: Integer $k$ (number of non-zero eigenvalues)
- `norm`: Float $\theta$ (perturbation strength)
- `pattern`: Enum {DIAGONAL, RANDOM_SPARSE, BLOCK_SPARSE}
- `sparsity_density`: Float $p \in (0, 1]$
- `support_indices`: Optional list of non-zero positions

## Relationships
- One `SimulationRun` has one `PerturbationConfig`
- One `PerturbationConfig` can be used in multiple `SimulationRun` instances

## Storage Format
- Raw matrices: `.npy` (dense) or `.npz` (sparse)
- Results: JSON with metadata
- Aggregated data: CSV for sweep results
- Checksums: JSON manifest in `state/checksums.json`
