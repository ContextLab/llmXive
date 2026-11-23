# Contracts and Interfaces

## Pipeline Stages

### Ingestion
- Input: HuggingFace Dataset (COD Organic)
- Output: `data/processed/crystal_dataset.csv`

### Splitting
- Input: `data/processed/crystal_dataset.csv`
- Output: `data/processed/split_indices.json`, `data/validation/scaffold_overlap_report.json`

### Training
- Input: Split data, Hyperparameters
- Output: `data/models/*.pkl`, `data/results/model_metrics.json`

### Interpretability
- Input: Trained models, Test data
- Output: `data/results/feature_importance_report.md`

## Error Handling
- `DownloadError`: Raised on network failure or missing dataset.
- `MemoryErrorHandled`: Raised when processing exceeds memory limits.
- `ValidationError`: Raised when data integrity checks fail.