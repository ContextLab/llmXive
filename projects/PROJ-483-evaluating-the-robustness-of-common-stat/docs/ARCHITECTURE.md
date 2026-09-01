# Architecture Overview

## Component Diagram

```
+----------------+ +----------------+ +------------------+
| config.py |------>| data_loader.py |------>| dependency_injector.py |
+----------------+ +----------------+ +------------------+
 | | |
 v v v
+----------------+ +----------------+ +------------------+
| main.py |<------| simulation_runner.py |<--| metrics.py |
+----------------+ +----------------+ +------------------+
 | | |
 v v v
+----------------+ +----------------+ +------------------+
| visualizer.py |<------| results/ |<------| data/ |
+----------------+ +----------------+ +------------------+
```

## Module Responsibilities

- **config.py**: Loads and validates `config.yaml`. Ensures all parameters are within expected ranges.
- **data_loader.py**: Fetches datasets from verified URLs. Validates data integrity and structure.
- **dependency_injector.py**: Implements AR(1), Block Bootstrap, and Spatial Kernel Smoothing. Validates injection quality.
- **simulation_runner.py**: Orchestrates the Monte Carlo loop. Generates null data, injects dependency, runs tests.
- **metrics.py**: Calculates Type I error rates, power, and confidence intervals. Trains logistic models.
- **visualizer.py**: Generates plots for error rate curves and power comparisons.
- **main.py**: Entry point. Coordinates the pipeline execution.

## Data Flow

1. **Configuration**: `config.yaml` is loaded by `config.py`.
2. **Data Fetching**: `data_loader.py` downloads datasets to `data/raw/`.
3. **Simulation**: `simulation_runner.py` generates synthetic data, injects dependency, and runs tests.
4. **Aggregation**: `metrics.py` aggregates results into `results/aggregated.csv`.
5. **Visualization**: `visualizer.py` reads aggregated results and generates plots.

## Error Handling

- **Data Integrity**: Checksums are verified. Mismatches raise `DataIntegrityError`.
- **Validation**: Datasets with $N < 50$ are skipped and logged.
- **Edge Cases**: Unconvergent models or invalid proxy qualities are logged and handled gracefully.

## Performance Considerations

- Vectorized operations (NumPy) are used for speed.
- Parallel processing is supported for independent simulation runs.
- Memory usage is monitored to prevent out-of-memory errors on large datasets.

## Extensibility

New dependency structures or statistical tests can be added by implementing the corresponding functions in `dependency_injector.py` or `simulation_runner.py` and registering them in `config.yaml`.
