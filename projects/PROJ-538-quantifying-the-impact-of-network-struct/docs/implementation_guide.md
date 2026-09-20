# Implementation Guide

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Data Ingestion │───▶│ Graph Builder │───▶│ Metric Extract │
└─────────────────┘ └─────────────────┘ └─────────────────┘
 │ │ │
 ▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Real/Synthetic │ │ Voronoi NN │ │ NetworkX Stats │
└─────────────────┘ └─────────────────┘ └─────────────────┘
 │ │ │
 └───────────┬───────────┴───────────┬───────────┘
 ▼ ▼
 ┌─────────────────┐ ┌─────────────────┐
 │ Correlation │ │ Visualization │
 │ Analyzer │ │ Engine │
 └─────────────────┘ └─────────────────┘
```

## Module Responsibilities

### `code/config.py`
- Defines `RunMode` enum (REAL, SYNTHETIC)
- Manages configuration paths and settings
- Controls mode selection flags

### `code/ingest.py`
- `DataAudit`: Queries external APIs for data availability
- `RealDataLoader`: Parses MD snapshots from real sources
- `SyntheticDataGenerator`: Generates synthetic snapshots
- `DefectGraphBuilder`: Constructs networks from atomic data
- `run_ingestion_pipeline`: Orchestrates data ingestion flow

### `code/synthetic.py`
- `ThermalConductivityEstimator`: Callaway model implementation
- `run_synthetic_generation`: Coordinates synthetic data creation

### `code/metrics.py`
- `MetricCalculator`: Computes topological descriptors
- Handles edge cases (disconnected graphs, undefined metrics)

### `code/stats.py`
- `CorrelationAnalyzer`: Pearson/Spearman correlation
- `run_post_hoc_power_analysis`: Statistical power evaluation
- Sensitivity analysis implementation

### `code/viz.py`
- `VisualizationEngine`: Generates plots and heatmaps
- `run_visualization_pipeline`: Orchestrates visualization flow

### `code/models.py`
- Pydantic models for data validation:
 - `AtomicSnapshot`: Raw atomic configuration
 - `DefectGraph`: Network representation
 - `CorrelationResult`: Statistical analysis output
 - `SensitivityResult`: Sensitivity analysis output
 - `PowerAnalysisResult`: Power analysis output

### `code/utils.py`
- Error classes: `DataAvailabilityError`, `VoronoiFailure`
- Logging utilities: `get_logger`, `log_audit_event`

### `code/interfaces.py`
- `IVoronoiNeighborFinder`: Abstract interface for neighbor detection

### `code/main.py`
- `run_pipeline`: Main orchestrator coordinating all components

## Data Flow

1. **Configuration**: Load settings from `code/config.py`
2. **Audit**: Check data availability via `DataAudit`
3. **Ingestion**:
 - If real data available: `RealDataLoader`
 - Else: `SyntheticDataGenerator`
4. **Graph Construction**: `DefectGraphBuilder` creates networks
5. **Metric Extraction**: `MetricCalculator` computes descriptors
6. **Statistical Analysis**: `CorrelationAnalyzer` performs tests
7. **Visualization**: `VisualizationEngine` generates plots
8. **Output**: Results written to `data/processed/`

## Error Handling Strategy

### Critical Errors
- `DataAvailabilityError`: Halt with specific message, switch to synthetic mode
- `VoronoiFailure`: Halt with error code, log to audit log

### Non-Critical Warnings
- Missing metadata: Log to audit log, continue with defaults
- Undefined metrics: Assign NaN, flag for review
- Small sample size: Log warning, continue analysis

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Verify edge case handling

### Integration Tests
- Test end-to-end pipeline execution
- Verify data flow between components
- Check output file generation

### Validation Tests
- Compare results against known benchmarks
- Verify statistical accuracy
- Ensure reproducibility

## Deployment Checklist

- [ ] All dependencies installed via `requirements.txt`
- [ ] Configuration files properly set up
- [ ] Data directories created (`data/raw/`, `data/processed/`, `data/contracts/`)
- [ ] Test suite passing (`pytest tests/ -v --cov=code`)
- [ ] Linting and formatting checks passed
- [ ] Real data source accessible (or synthetic mode configured)
- [ ] Output files generated correctly
- [ ] Documentation complete and accurate

## Troubleshooting

### Common Issues

#### Data Fetch Failures
- **Symptom**: `DataAvailabilityError` raised
- **Solution**: Check network connectivity, verify API credentials, or rely on synthetic mode

#### Voronoi Tessellation Errors
- **Symptom**: `VoronoiFailure` exception
- **Solution**: Verify periodic boundary conditions data, check atomic coordinates

#### Memory Constraints
- **Symptom**: Out-of-memory errors with large datasets
- **Solution**: Enable streaming mode, process data in chunks

#### Statistical Analysis Warnings
- **Symptom**: Low power, small sample size warnings
- **Solution**: Increase sample size if possible, acknowledge limitations in results

## Performance Considerations

- Voronoi tessellation is computationally intensive; cache results where possible
- Graph construction scales with O(N log N) for N atoms
- Statistical analysis is linear in number of graphs
- Visualization generation is independent per graph

## Future Enhancements

- Support for additional alloy systems
- Advanced machine learning models for conductivity prediction
- Real-time monitoring of pipeline execution
- Interactive visualization dashboard
- Parallel processing for large-scale datasets
