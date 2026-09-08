# API Reference

This document provides a reference for the core modules and classes in the `code/` directory.

## `code/config.py`

Manages project configuration and execution modes.

### Classes

- **`RunMode`** (Enum): Defines execution modes (`REAL`, `SYNTHETIC`).
- **`Config`**: Holds configuration parameters (paths, mode, thresholds).

### Usage

```python
from config import Config, RunMode

cfg = Config(mode=RunMode.SYNTHETIC)
```

## `code/models.py`

Defines Pydantic models for data structures.

### Classes

- **`AtomicSnapshot`**: Represents an MD snapshot (species, coordinates, box, metadata).
- **`DefectGraph`**: Represents the constructed defect network (nodes, edges, metrics).
- **`CorrelationResult`**: Stores correlation analysis results.
- **`SensitivityResult`**: Stores sensitivity analysis results.
- **`PowerAnalysisResult`**: Stores power analysis results.

## `code/ingest.py`

Handles data ingestion and graph construction.

### Classes

- **`DataAudit`**: Audits data availability from external APIs.
- **`RealDataLoader`**: Loads real MD snapshots from disk or APIs.
- **`SyntheticDataGenerator`**: Generates synthetic snapshots.
- **`ThermalConductivityEstimator`**: Estimates conductivity via Callaway model.
- **`DefectGraphBuilder`**: Constructs defect graphs using Voronoi tessellation.

### Functions

- **`run_ingestion_pipeline()`**: Orchestrates the ingestion process.

## `code/metrics.py`

Computes topological metrics for defect graphs.

### Classes

- **`MetricCalculator`**: Calculates clustering coefficient, mean degree, degree moments, and percolation threshold.

## `code/stats.py`

Performs statistical analysis.

### Classes

- **`CorrelationAnalyzer`**: Computes Pearson/Spearman correlations with Bonferroni correction.

### Functions

- **`run_post_hoc_power_analysis()`**: Calculates minimum detectable effect size.

## `code/viz.py`

Generates visualizations.

### Classes

- **`VisualizationEngine`**: Creates scatter plots and heatmaps.

## `code/utils.py`

Utility functions and custom exceptions.

### Exceptions

- **`DataAvailabilityError`**: Raised when real data is unavailable.
- **`VoronoiFailure`**: Raised when Voronoi tessellation fails.

### Functions

- **`get_logger()`**: Retrieves a configured logger.
- **`log_audit_event()`**: Logs events to `data/audit_log.json`.
