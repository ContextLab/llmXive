# Data Model: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

## Dataset Schema

The MulTaBench datasets are multimodal, containing both tabular and text/image features. The schema is defined by the `multabench.datasets` module.

**General Schema**:
- `dataset_id`: str (Unique identifier, e.g., "BIN_TEXT_FAKE_JOB_POSTING")
- `modality`: str ("text", "image", "multimodal")
- `task_type`: str ("classification", "regression")
- `features`: dict (Contains "tabular", "text", "image" keys with corresponding data)
- `target`: array (Labels)

**Example Data Structure** (Conceptual):
```json
{
  "dataset_id": "BIN_TEXT_FAKE_JOB_POSTING",
  "modality": "text",
  "task_type": "classification",
  "features": {
    "tabular": {"num_rows": 1000, "num_cols": 10},
    "text": ["job description 1", "job description 2", ...]
  },
  "target": [0, 1, ...]
}
```

## Output Schema

The benchmark produces a results CSV file containing performance metrics.

**Schema**: `results.csv`
- `dataset_id`: str
- `model_id`: str
- `config`: str ("frozen" or "tuned")
- `metric_name`: str ("accuracy", "auc", "mse")
- `metric_value`: float
- `timestamp`: str (ISO 8601)

**Constraints**:
- `metric_value` must be numeric.
- For classification metrics (accuracy, auc), `0.0 <= metric_value <= 1.0`.
- For regression metrics (mse), `metric_value >= 0.0`.

## Data Flow

1. **Input**: Dataset registry (from `multabench.datasets.all_datasets`).
2. **Processing**:
   - Load dataset (with error handling).
   - Preprocess features (tokenization for text, resizing for images).
   - Split into train/test.
   - Train/Evaluate model (frozen vs. tuned).
3. **Output**: Metrics appended to `results.csv`.

## Assumptions

- The `multabench` library correctly handles the loading of multimodal data.
- The dataset IDs used in the configuration match those in the registry.
- The output CSV format is consistent with the paper's reporting.
