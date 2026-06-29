# Download Module

This module handles the retrieval of educational datasets required for the neuro-symbolic learning pipeline.

## Usage

```python
from code.download import fetch_assistments_dataset

# Fetch the dataset (with automatic fallback to synthetic if needed)
df = fetch_assistments_dataset()
```

## Data Sources

1. **Remote**: Attempts to fetch from the configured `REMOTE_URL`.
2. **Cache**: Checks `data/raw/assistments_sample.csv`.
3. **Synthetic**: If all else fails, generates a synthetic dataset mimicking the ASSISTments schema.

## Output

- `data/raw/assistments_sample.csv`: Cached real data (if successful).
- `data/raw/assistments_synthetic_fallback.csv`: Synthetic data (if fallback triggered).