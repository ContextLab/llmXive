# Quickstart: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Prerequisites

- Python 3.11+
- Git
- Access to the Z-Reward dataset (MUST be present in `data/raw/z_reward.parquet`)

## Setup

1. **Clone and Install**
   ```bash
   git checkout 001-llmxive-entanglement-analysis
   cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
   pip install -r requirements.txt
   ```

2. **Prepare Data (MANDATORY)**
   The Z-Reward dataset MUST be placed in `data/raw/z_reward.parquet`.
   If the file is missing, the pipeline will fail with a clear error message.
   ```bash
   cp /path/to/z_reward.parquet data/raw/
   ```

3. **Run the Pipeline**
   Execute the full pipeline from ingestion to model training:
   ```bash
   python code/ingest.py
   python code/features.py
   python code/train.py
   ```

4. **View Results**
   Check `results/results.json` for R², MAE, p-values.
   Check `results/covariance_matrix.json` for the global covariance matrix.
   Check `results/exclusion_log.csv` for excluded samples.
   Check `results/lineage_report.csv` for per-sample target source verification.
   ```bash
   cat results/results.json
   ```

## Running Tests

```bash
pytest tests/
```

## Troubleshooting

- **Missing Data**: If `data/raw/z_reward.parquet` is missing, the script will fail with "Required dataset Z-Reward not found".
- **Memory Error**: If the dataset is too large, the script will automatically sample the first [deferred] rows (configurable in `code/utils.py`).
- **Missing Annotations**: Samples with missing human annotations are excluded and logged in `results/exclusion_log.csv`.
