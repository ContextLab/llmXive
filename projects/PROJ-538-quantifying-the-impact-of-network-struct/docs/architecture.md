# Architecture Overview

## Pipeline Flow

1. **Configuration**: `code/config.py` sets the execution mode (Real vs. Synthetic).
2. **Data Ingestion**:
 - If `REAL`: `DataAudit` checks APIs; `RealDataLoader` fetches data.
 - If `SYNTHETIC`: `SyntheticDataGenerator` creates snapshots.
 - `ThermalConductivityEstimator` assigns conductivity values.
3. **Graph Construction**: `DefectGraphBuilder` creates defect networks using Voronoi NN.
4. **Metric Extraction**: `MetricCalculator` computes topological descriptors.
5. **Statistical Analysis**: `CorrelationAnalyzer` correlates metrics with conductivity.
6. **Visualization**: `VisualizationEngine` generates plots.
7. **Reporting**: Results are saved to `data/processed/` and logged to `data/audit_log.json`.

## Data Model

- **AtomicSnapshot**: Raw atomic positions and species.
- **DefectGraph**: NetworkX graph with nodes (atoms) and edges (mismatched neighbors).
- **Results**: Pydantic models for correlations, sensitivity, and power analysis.

## Error Handling

- **DataAvailabilityError**: Triggers switch to Synthetic Mode.
- **VoronoiFailure**: Halts execution with specific error code.
- **Edge Cases**: Handled gracefully (N=1, missing metadata) with logging.

## Extensibility

- New data sources can be added by implementing `RealDataLoader`.
- New metrics can be added to `MetricCalculator`.
- New visualization types can be added to `VisualizationEngine`.
