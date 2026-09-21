# Implementation Notes & Developer Guide

## Module Overview

### `code/data/preprocess.py`
- Wraps fMRIPrep with memory-efficient settings (float32).
- Handles behavioral metric extraction from metadata.
- Enforces retention gates (80% threshold) and power checks (N < 85).

### `code/analysis/centrality.py`
- Loads connectivity matrices for the full AAL3 atlas.
- Computes degree, betweenness, and eigenvector centrality using `networkx`.
- Aggregates regional metrics into a global score.
- Calculates Mean FD and VIF for predictor selection.

### `code/analysis/regression.py`
- Merges behavioral, centrality, and motion data.
- Fits linear regression and GAM models.
- Generates scatter plots and model summaries.
- Implements baseline R² calculation for null models.

### `code/analysis/validation.py`
- Executes Freedman-Lane permutation tests.
- Performs k-fold cross-validation.
- Generates null distribution histograms and empirical p-values.

## Configuration Management
All hyperparameters are defined in `code/utils/config.py`. Use `get_config()` to retrieve the singleton configuration object. Do not hardcode paths or thresholds.

## Error Handling
- **Data Missing**: Scripts fail loudly if required columns (e.g., `pre_motor_score`) are missing.
- **Retrieval Failure**: Data loaders do not fall back to synthetic data; they raise exceptions.
- **VIF Check**: If VIF > 5, the pipeline automatically switches to a PCA-based predictor set.

## Testing Strategy
- **Contract Tests**: Validate data schemas (CSV columns, JSON keys).
- **Integration Tests**: Verify end-to-end data flow between modules.
- **Unit Tests**: Isolate specific functions (e.g., centrality calculation logic).

## Performance Considerations
- Use `float32` for large matrices to reduce memory footprint.
- Stream data processing where possible (e.g., chunked CSV reading).
- Parallelize subject-level processing if running on a multi-core machine.
