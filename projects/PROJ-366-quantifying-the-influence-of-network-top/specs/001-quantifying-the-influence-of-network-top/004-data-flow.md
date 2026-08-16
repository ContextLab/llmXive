# Data Flow and Artifact Lifecycle

This document describes the end-to-end flow of data through the pipeline, from
raw input to final analysis results. It details the lifecycle of each major
artifact, including generation, validation, and consumption.

## Pipeline Stages

The pipeline consists of four main stages:

1. **Ingestion**: Convert raw XYZ files to atomic graphs.
2. **Simulation**: Run Green-Kubo simulations to obtain thermal conductivity.
3. **Modeling**: Train GNNs and extract feature importance.
4. **Analysis**: Perform statistical correlation and mixed-effects modeling.

## Stage 1: Ingestion

**Input**: Raw XYZ files from `data/raw/` (e.g., amorphous silicon configurations).

**Process**:
- `code/ingest/graph_builder.py` reads XYZ files.
- Constructs `AtomicGraph` objects using a 3.0 Å bond cutoff.
- Calculates node degrees and clustering coefficients.
- Validates against `atomic_graph.schema.yaml`.

**Output**:
- Serialized graphs: `data/processed/graphs/<sample_id>.pkl`
- Node degree statistics: `data/processed/graphs/node_degree_stats.json`
- Excluded samples list: `data/processed/graphs/excluded_samples.json` (if defects > 15%)

**Validation**:
- `code/ingest/validators.py` ensures schema compliance.
- `code/ingest/graph_serializer.py` generates checksums.

**Next Stage**: Simulation (requires valid graphs).

## Stage 2: Simulation

**Input**: Serialized graphs from `data/processed/graphs/`.

**Process**:
- `code/simulation/green_kubo.py` runs LAMMPS simulations.
- Computes heat current autocorrelation function (HCACF).
- Checks for convergence (relative change < 1%).
- Calculates thermal conductivity.

**Output**:
- Thermal samples: `data/processed/conductivities/<sample_id>.pkl`
- Convergence status: `data/processed/conductivities/convergence_status.json`
- Convergence report: `data/processed/conductivities/convergence_report.json`

**Validation**:
- `code/simulation/thermal_sample_saver.py` validates against `thermal_sample.schema.yaml`.
- `code/simulation/conductivity_validator.py` checks values against literature range.

**Next Stage**: Modeling (requires converged samples).

## Stage 3: Modeling

**Input**:
- Valid graphs from Stage 1.
- Converged thermal samples from Stage 2.

**Process**:
- `code/model/gnn.py` defines the GNN architecture.
- `code/model/trainer.py` trains the model to predict local heat flux.
- `code/model/feature_importance.py` computes SHAP values.

**Output**:
- SHAP values: `data/processed/model_outputs/shap_values.npy`
- GNN results: `data/processed/model_outputs/gnn_results.json`
- Power analysis: `data/processed/model_outputs/power_analysis.json` (if N >= 10)

**Validation**:
- `code/model/trainer.py` checks for loss convergence.
- `code/model/feature_importance.py` validates SHAP output shape.

**Next Stage**: Analysis (requires SHAP values and conductivity data).

## Stage 4: Analysis

**Input**:
- SHAP values from Stage 3.
- Thermal conductivity data from Stage 2.

**Process**:
- `code/analysis/pearson_correlation.py` computes Pearson correlation.
- `code/analysis/correlation_significance.py` applies Bonferroni correction.
- `code/analysis/lmm_analysis.py` performs Linear Mixed-Effects modeling.
- `code/analysis/final_results_aggregator.py` aggregates all results.

**Output**:
- Pearson correlation: `data/processed/model_outputs/correlation_pearson.json`
- Corrected correlation: `data/processed/model_outputs/correlation_pearson_corrected.json`
- LMM results: `data/processed/model_outputs/lmm_results.json`
- Final aggregated results: `data/processed/model_outputs/final_results.json`

**Validation**:
- `code/analysis/power_checker.py` ensures N >= 10 before proceeding.
- `code/analysis/checksum_verifier.py` verifies all output artifacts.

## Artifact Lifecycle Summary

| Artifact | Stage | Format | Validation |
|----------|-------|--------|------------|
| `data/raw/*.xyz` | Input | XYZ | File exists, valid format |
| `data/processed/graphs/*.pkl` | Ingestion | Pickle | `atomic_graph.schema.yaml` |
| `data/processed/conductivities/*.pkl` | Simulation | Pickle | `thermal_sample.schema.yaml` |
| `data/processed/model_outputs/shap_values.npy` | Modeling | NumPy | Shape matches (N, features) |
| `data/processed/model_outputs/*.json` | Analysis | JSON | Schema compliance |
| `data/checksums.json` | All | JSON | SHA-256 match |

## Error Propagation

- **Ingestion Failure**: Stops pipeline. No graphs, no simulation.
- **Simulation Failure**: Sample excluded. Pipeline continues with remaining samples.
- **Power Check Failure**: Stops pipeline if N < 10.
- **Analysis Failure**: Logs error, but may proceed with partial results if configured.

## Data Retention

- **Raw Data**: Retained indefinitely.
- **Processed Graphs**: Retained for re-use in modeling.
- **Simulation Outputs**: Retained for audit and re-analysis.
- **Model Outputs**: Retained for final reporting.
- **Logs**: Retained for debugging (see `code/__init__.py`).

## Security and Integrity

- All serialized artifacts are checksummed.
- Checksums are verified at the start of each stage.
- Invalid data triggers immediate halt to prevent corruption.

## Future Enhancements

- **Streaming**: For large datasets, implement streaming ingestion to reduce memory footprint.
- **Parallelization**: Parallelize simulation and modeling stages across multiple cores.
- **Visualization**: Add tools to visualize graph structures and correlation results.

## References

- **Schema Docs**: `002-data-models.md`
- **Schema Contracts**: `003-schema-overview.md`
- **Spec**: `specs/001-topology-thermal-conductivity/spec.md`
