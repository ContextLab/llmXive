# Architecture Overview

## System Components

### Data Ingestion Layer
- **`download.py`**: Fetches raw data from external APIs (Materials Project, OpenKIM)
- **`utils.py`**: Provides checksumming, logging, and seed management utilities
- **`error_handling.py`**: Manages data insufficiency errors and exit codes

### Processing Layer
- **`geometry_parser.py`**: Parses crystallographic files and extracts geometric features
- **`preprocess.py`**: Validates features, tags metadata, enforces constraints
- **`diagnostics.py`**: Computes mutual information for feature analysis

### Modeling Layer
- **`train.py`**: Trains XGBoost model with hyperparameter tuning
- **`validate.py`**: Performs cross-validation and bias testing
- **`interpret.py`**: Generates SHAP analysis and sensitivity tables

### Infrastructure
- **`models/grain_boundary_record.py`**: Dataclass for grain boundary records
- **`optimization_utils.py`**: Vectorized operations for performance
- **`config/`**: Configuration modules for thresholds and linting

## Data Flow

```
External APIs (Materials Project, OpenKIM)
 ↓
[download.py] → data/raw/ (raw files + checksums)
 ↓
[geometry_parser.py] → data/processed/parsed_geometry.parquet
 ↓
[preprocess.py] → data/processed/cleaned_dataset.parquet
 ↓
[diagnostics.py] → artifacts/reports/collinearity_diagnostic.json
 ↓
[train.py] → models/best_model.json + artifacts/reports/training_metrics.json
 ↓
[validate.py] → artifacts/reports/validation_report.json
 ↓
[interpret.py] → artifacts/figures/ + artifacts/reports/threshold-variation-table.csv
```

## File Organization

```
PROJ-117-quantifying-the-impact-of-grain-boundary/
├── code/
│ ├── download.py
│ ├── geometry_parser.py
│ ├── preprocess.py
│ ├── diagnostics.py
│ ├── train.py
│ ├── validate.py
│ ├── interpret.py
│ ├── utils.py
│ ├── error_handling.py
│ ├── optimization_utils.py
│ ├── models/
│ │ └── grain_boundary_record.py
│ └── config/
│ ├── linting_config.py
│ ├── setup_linting.py
│ └── threshold_config.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── metadata.yaml
├── models/
│ └── best_model.json
├── artifacts/
│ ├── reports/
│ └── figures/
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
│ ├── api_reference.md
│ ├── data_schema.md
│ ├── quickstart.md
│ └── architecture.md
├── README.md
├── requirements.txt
├──.env (not committed)
└── state.yaml
```

## Design Decisions

### Why XGBoost?
- Gradient boosting provides strong performance on tabular data
- Built-in handling of feature interactions
- SHAP integration for interpretability

### Why Parquet?
- Efficient columnar storage format
- Preserves data types
- Faster I/O than CSV for large datasets

### Why 70/15/15 Split?
- Sufficient training data for XGBoost
- Adequate validation set for hyperparameter tuning
- Representative test set for final evaluation

### Why n ≥ 500?
- Minimum sample size for reliable statistical validation
- Ensures sufficient data for k-fold cross-validation
- Aligns with community standards for materials property prediction

## Performance Considerations

### CPU-Only Execution
- All operations use vectorized NumPy/Pandas
- No GPU dependencies
- Designed for 2-core CI environments

### Memory Constraints
- Streaming support for large datasets
- Chunked processing where applicable
- Target: <7GB RAM usage

### Runtime Budget
- Target: <6 hours for full pipeline
- Parallelizable tasks identified in tasks.md
- Early termination on data insufficiency
