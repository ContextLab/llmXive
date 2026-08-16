# Schema Overview and Contracts

This document provides a high-level overview of the schema contracts used in the
project. It is intended for developers and data engineers to understand the data
flow and validation requirements.

## Purpose

The `contracts/` directory contains YAML schema definitions that serve as the
single source of truth for data structures. These schemas are used to:

1. **Validate Input Data**: Ensure that ingested data (e.g., XYZ files, simulation logs)
 conforms to expected formats before processing.
2. **Enforce Output Consistency**: Guarantee that all pipeline stages produce data
 that can be consumed by downstream stages.
3. **Document Data Models**: Provide a machine-readable and human-readable description
 of the data.

## Schema Files

The following schema files are defined in the `contracts/` directory:

1. **`atomic_graph.schema.yaml`**
 - **Target**: `data/processed/graphs/*.pkl`
 - **Validator**: `code/ingest/validators.py` (load_and_validate)
 - **Key Constraints**:
 - Nodes must have 3D coordinates.
 - Edges must be pairs of valid node indices.
 - Coordination number (degree) is critical for defect detection.

2. **`thermal_sample.schema.yaml`**
 - **Target**: `data/processed/conductivities/*.pkl`
 - **Validator**: `code/simulation/thermal_sample_saver.py`
 - **Key Constraints**:
 - `conductivity` must be a positive float.
 - `converged` must be a boolean.
 - `metadata` must contain simulation parameters.

3. **`gnn_output.schema.yaml`**
 - **Target**: `data/processed/model_outputs/gnn_results.json`
 - **Validator**: `code/model/feature_importance.py` (implicit via usage)
 - **Key Constraints**:
 - `predicted_flux` must be a 1D array of floats.
 - `loss` must be a non-negative float.

## Validation Workflow

1. **Ingestion**:
 - `code/ingest/graph_builder.py` constructs an `AtomicGraph` object.
 - `code/ingest/validators.py` validates the object against `atomic_graph.schema.yaml`.
 - If validation fails, the process halts with `ERR-002`.

2. **Simulation**:
 - `code/simulation/green_kubo.py` produces raw simulation data.
 - `code/simulation/thermal_sample_saver.py` wraps the data into a `ThermalSample` object.
 - Validation occurs before saving to `data/processed/conductivities/`.

3. **Modeling**:
 - `code/model/trainer.py` produces model outputs.
 - `code/model/feature_importance.py` extracts SHAP values.
 - Results are validated against `gnn_output.schema.yaml` before aggregation.

## Error Handling

The pipeline uses specific error codes for data validation failures:

- **ERR-001**: Input file missing or corrupted (e.g., invalid XYZ format).
- **ERR-002**: Schema validation failure (data does not match contract).
- **ERR-003**: Checksum mismatch (data integrity compromised).

When an error occurs, the pipeline logs the error code and halts execution to
prevent propagation of invalid data.

## Extensibility

New schemas can be added to the `contracts/` directory by:
1. Defining the YAML schema.
2. Updating `code/ingest/validators.py` to include the new schema.
3. Updating this documentation.

The `pyyaml` library is used for schema loading and validation.
The `jsonschema` library is used for runtime validation.

## Maintenance

- **Versioning**: Schema versions should be tracked in the `contracts/` directory
 if breaking changes are introduced.
- **Backward Compatibility**: New fields should be optional where possible to
 maintain compatibility with older data.
- **Testing**: Contract tests in `tests/contract/test_schemas.py` ensure that
 schemas are valid and loaders function correctly.

## Contact

For questions regarding data models or schema definitions, refer to the
`specs/001-topology-thermal-conductivity/` directory or the project maintainers.
