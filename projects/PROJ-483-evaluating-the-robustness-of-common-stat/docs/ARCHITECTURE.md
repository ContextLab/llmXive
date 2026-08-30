# Architecture Documentation

## System Overview
The `PROJ-483` pipeline is designed to rigorously evaluate the impact of non-independence on statistical test validity. It follows a modular, data-centric architecture.

## Core Components

### 1. Configuration (`code/config.py`)
- **Role**: Centralized loading and validation of simulation parameters.
- **Mechanism**: Uses `yaml` to load `code/config.yaml` and validates against `contracts/simulation_config.schema.yaml`.
- **Key Output**: A validated dictionary of parameters used across all modules.

### 2. Data Layer (`code/data_loader.py`)
- **Role**: Manages the lifecycle of input datasets.
- **Workflow**:
 1. Reads `data/manifests/datasets.yaml` for verified URLs.
 2. Fetches data via `requests`.
 3. Validates structure (N >= 50, variable types).
 4. Saves raw CSVs to `data/raw/` and computes checksums.
- **Error Handling**: Raises `CriticalValidationError` if validation fails, preventing downstream execution with invalid data.

### 3. Dependency Injection (`code/dependency_injector.py`)
- **Role**: Introduces controlled non-independence into data.
- **Methods**:
 - **AR(1)**: Temporal autocorrelation with tunable strength $r$.
 - **Block Bootstrap**: Hierarchical dependency with tunable block size.
 - **Spatial Kernel**: Spatial dependency using feature-space clustering for datasets without coordinates.
- **Validation**: Each injection method includes a validation routine to ensure the resulting dependency matches the target parameter within tolerance.

### 4. Simulation Engine (`code/simulation_runner.py`)
- **Role**: Executes the Monte Carlo loop.
- **Algorithm**:
 1. **Generate**: Create synthetic data under the true null hypothesis (e.g., Normal(0,1)).
 2. **Inject**: Apply a dependency structure (AR(1), Block, Spatial).
 3. **Test**: Perform the statistical test (t-test, ANOVA, Chi-squared).
 4. **Record**: Store the p-value.
- **Edge Cases**: Implements logic to handle datasets where null construction is impossible or assumptions are violated, logging to `results/edge_case_report.json`.

### 5. Metrics & Analysis (`code/metrics.py`)
- **Role**: Aggregates raw p-values into meaningful statistics.
- **Functions**:
 - `calculate_type1_error`: Computes false positive rate with Clopper-Pearson CI.
 - `calculate_power`: Computes power under alternative hypotheses.
 - `train_logistic_model`: Fits a model to predict error rate from dependency strength.
 - `verify_trend_monotonicity`: Checks for monotonic increase in error rates.

### 6. Visualization (`code/visualizer.py`)
- **Role**: Generates publication-quality plots.
- **Outputs**: Error rate curves, power comparisons, and confidence interval bands.

## Data Flow
1. **Input**: `code/config.yaml` + `data/manifests/datasets.yaml`.
2. **Fetch**: `data_loader.py` -> `data/raw/`.
3. **Simulate**: `simulation_runner.py` -> `results/simulation_raw.csv`.
4. **Aggregate**: `metrics.py` -> `results/aggregated.csv`.
5. **Visualize**: `visualizer.py` -> `figures/`.

## Testing Strategy
- **Unit Tests**: Validate individual functions (e.g., AR(1) injection accuracy).
- **Integration Tests**: Ensure the pipeline produces expected output schemas.
- **Contract Tests**: Verify CSV and JSON schema compliance.

## Extensibility
- New dependency models can be added to `dependency_injector.py`.
- New statistical tests can be integrated into `simulation_runner.py`.
- New metrics can be defined in `metrics.py`.
