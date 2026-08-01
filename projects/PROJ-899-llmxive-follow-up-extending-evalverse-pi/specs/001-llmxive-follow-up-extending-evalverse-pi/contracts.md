# Contracts: llmXive Feature Distillation

## API Contracts

### Data Fetching
- **Input**: None
- **Output**: `data/raw/` directory populated with dataset files.
- **Contract**: `fetch_evalverse_dataset()` must download and unzip the dataset.

### Feature Extraction
- **Input**: Path to video file.
- **Output**: `FeatureVector` object or dictionary.
- **Contract**: Must handle missing audio gracefully (return zero/null vectors).

### Model Training
- **Input**: `FeatureVector` dataset, `DimensionScore` labels.
- **Output**: Trained model objects (Ridge, Lasso, XGBoost).
- **Contract**: Must save model artifacts to `data/results/`.

### Correlation Calculation
- **Input**: Features, Scores.
- **Output**: `CorrelationResult` for each dimension.
- **Contract**: Must calculate Pearson, Spearman, and 95% CI via bootstrapping.

### Feasibility Profiling
- **Input**: Batch of clips.
- **Output**: Memory usage (MB), Time (s).
- **Contract**: Must log exact values to `data/profiling_logs.json`.

## Error Handling Contracts
- **Data Fetch Failure**: Raise `FileNotFoundError` if download fails.
- **Feature Extraction Failure**: Log warning, return zero vector, continue.
- **Gate Failure**: Exit with code 1 and log specific reason.
