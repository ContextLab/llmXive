# Data Models and Schema Documentation

This document describes the data models, schemas, and file formats used in the
"Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon"
pipeline.

All data artifacts produced by the pipeline conform to the schemas defined in the
`contracts/` directory. This document provides a human-readable summary of those
schemas, their fields, types, and semantic meaning.

## 1. Atomic Graph Schema

**Schema File**: `contracts/atomic_graph.schema.yaml`

**Purpose**: Represents the atomic structure of a pre-equilibrated amorphous silicon
sample as a graph. Nodes correspond to atoms; edges correspond to bonds defined by
a distance cutoff (default 3.0 Å).

**Output Location**: `data/processed/graphs/<sample_id>.pkl` (pickle format)

**Schema Definition**:

```yaml
type: object
required:
 - graph_id
 - nodes
 - edges
properties:
 graph_id:
 type: string
 description: Unique identifier for the sample (matches source XYZ filename).
 nodes:
 type: array
 description: List of atomic nodes.
 items:
 type: object
 required:
 - id
 - coords
 - degree
 - clustering_coeff
 properties:
 id:
 type: integer
 description: Unique node index (0-based).
 coords:
 type: array
 items:
 type: number
 format: float32
 minItems: 3
 maxItems: 3
 description: Cartesian coordinates (x, y, z) in Angstroms.
 degree:
 type: integer
 description: Number of bonds (neighbors) for this atom.
 clustering_coeff:
 type: number
 format: float32
 description: Local clustering coefficient (0.0 to 1.0).
 edges:
 type: array
 description: List of undirected edges as pairs of node indices.
 items:
 type: array
 items:
 type: integer
 minItems: 2
 maxItems: 2
```

**Key Fields**:
- `nodes.degree`: Used for topological defect detection (coordination number).
- `nodes.clustering_coeff`: Measures local connectivity density.

## 2. Thermal Sample Schema

**Schema File**: `contracts/thermal_sample.schema.yaml`

**Purpose**: Encapsulates the results of a Green-Kubo simulation for a single
atomic graph, including the computed thermal conductivity and convergence status.

**Output Location**: `data/processed/conductivities/<sample_id>.pkl` (pickle format)

**Schema Definition**:

```yaml
type: object
required:
 - graph_id
 - conductivity
 - converged
 - metadata
properties:
 graph_id:
 type: string
 description: Reference to the source AtomicGraph.
 conductivity:
 type: number
 format: float64
 description: Thermal conductivity in W/(m·K).
 converged:
 type: boolean
 description: True if the heat current autocorrelation function converged
 (relative change < 1% in final segment).
 metadata:
 type: object
 description: Simulation metadata and diagnostics.
 properties:
 simulation_time_ps:
 type: number
 temperature_K:
 type: number
 potential:
 type: string
 description: Interatomic potential used (e.g., "Stillinger-Weber").
 hcacf_samples:
 type: integer
 description: Number of samples in the heat current autocorrelation.
```

**Key Fields**:
- `converged`: Critical for data integrity; non-converged samples are excluded
 from statistical analysis.
- `conductivity`: The ground-truth label for the GNN model.

## 3. GNN Output Schema

**Schema File**: `contracts/gnn_output.schema.yaml`

**Purpose**: Stores the output of the Graph Neural Network training and inference,
including predicted flux vectors and loss metrics.

**Output Location**: `data/processed/model_outputs/gnn_results.json`

**Schema Definition**:

```yaml
type: object
required:
 - predicted_flux
 - loss
 - epoch
properties:
 predicted_flux:
 type: array
 description: Predicted local heat flux vector for each atom.
 items:
 type: number
 format: float32
 loss:
 type: number
 format: float32
 description: Final training loss (MSE).
 epoch:
 type: integer
 description: Number of training epochs completed.
```

## 4. Derived Data Artifacts

The pipeline generates several derived artifacts that do not strictly conform to
the object schemas above but are critical for analysis.

### 4.1 Node Degree Statistics
**File**: `data/processed/graphs/node_degree_stats.json`
**Content**: Aggregated statistics of atomic coordination numbers across all samples.
```json
{
 "mode": 4,
 "mean": 4.02,
 "std": 0.85,
 "sample_count": 15,
 "total_atoms": 4500
}
```

### 4.2 Convergence Status
**File**: `data/processed/conductivities/convergence_status.json`
**Content**: Boolean map of sample IDs to convergence status.
```json
{
 "sample_01": true,
 "sample_02": false
}
```

### 4.3 Excluded Samples
**File**: `data/processed/graphs/excluded_samples.json`
**Content**: List of sample IDs excluded due to topological defects (>15% atoms with coordination <3 or >6).
```json
["sample_05", "sample_09"]
```

### 4.4 Correlation Results
**File**: `data/processed/model_outputs/correlation_pearson_corrected.json`
**Content**: Pearson correlation coefficients and p-values with Bonferroni correction.
```json
{
 "r": 0.65,
 "p_value": 0.012,
 "n_samples": 15,
 "method": "pearson",
 "corrected_p_value": 0.036,
 "significant": true
}
```

### 4.5 Checksum Manifest
**File**: `data/checksums.json`
**Content**: SHA-256 checksums for all serialized artifacts to ensure data integrity.
```json
{
 "data/processed/graphs/sample_01.pkl": "a1b2c3...",
 "data/processed/conductivities/sample_01.pkl": "d4e5f6..."
}
```

## 5. File Formats

- **Pickle (`.pkl`)**: Used for complex Python objects (graphs, thermal samples).
 Serialized using `pickle` protocol 4.
- **JSON (`.json`)**: Used for configuration, statistics, and correlation results.
- **NumPy (`.npy`)**: Used for large arrays (e.g., SHAP values).

## 6. Validation

All artifacts are validated against their respective schemas upon loading.
The `code/ingest/validators.py` module provides the validation logic.
If a file fails validation, the pipeline halts with a specific error code.

- **ERR-001**: Corrupted or missing input file.
- **ERR-002**: Schema validation failure.
- **ERR-003**: Checksum mismatch.

## 7. Data Integrity

Checksums are generated for all serialized artifacts using SHA-256.
The `data/checksums.json` file serves as a manifest for verification.
The `code/analysis/checksum_verifier.py` module can be used to verify integrity.

## 8. References

- **Spec**: `specs/001-topology-thermal-conductivity/spec.md`
- **Plan**: `plan.md`
- **Schemas**: `contracts/` directory.
