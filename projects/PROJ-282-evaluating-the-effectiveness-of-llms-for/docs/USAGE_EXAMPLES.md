# Usage Examples

## Running the Full Pipeline

```bash
python code/src/main.py
```

This will:
1. Validate the environment (CPU check).
2. Select the best CPU-compatible model.
3. Download and process datasets.
4. Run inference and static analysis.
5. Generate final reports.

## Running a Specific Stage

### Data Ingestion
```bash
python code/scripts/run_download_vuldeepecker.py
python code/scripts/run_download_jsvulndb.py
python code/scripts/run_download_juliet.py
```

### Feature Extraction
```bash
python code/scripts/run_feature_extraction.py
```

### Inference
```bash
python code/scripts/run_llm_inference.py
```

### Analysis
```bash
python code/scripts/run_analysis.py
```

## Custom Configuration

Modify `src/utils/config.py` to change:
- `SEED`: Random seed for reproducibility.
- `MAX_BATCH_SIZE`: Initial batch size estimate.
- `TIME_BUDGET`: Total runtime limit (default: 6 hours).

## Inspecting Results

- **Predictions**: `data/results/llm_predictions_raw.json`
- **Metrics**: `data/results/metrics.json`
- **Logs**: `data/logs/`
- **Final Report**: `research.md`

## Troubleshooting Common Issues

- **Out of Memory**: Reduce `MAX_BATCH_SIZE` in `config.py`.
- **Slow Inference**: Ensure no other heavy processes are running.
- **Data Fetch Errors**: Check network connection and dataset URLs.
