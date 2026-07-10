# Quickstart: llmXive follow-up: extending "Orca: The World is in Your Mind"

## Prerequisites
- Python 3.11+
- 7GB+ RAM
- Git
- (Optional) `mujoco` or `pybullet` for physics simulation.

## Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor
pip install -r requirements.txt
```

### 2. Verify Dataset Availability
Run the data availability check:
```bash
python code/data/check_data_availability.py
```
*Note: If this script fails due to missing verified video sources, the project will automatically switch to a verified synthetic fallback (e.g., CLEVR). If no fallback is available, the project halts.*

### 3. Run the Pipeline
Execute the full pipeline (Download -> Extract -> Verify -> Train -> Analyze):
```bash
python code/run_full_pipeline.py
```

### 4. Run Tests
```bash
pytest tests/
```

## Expected Outputs
- `data/processed/model_results.csv`: Contains accuracy metrics for all models.
- `data/processed/stats_report.json`: Contains p-values, sensitivity scores, and `verified_ratio`.
- `data/logs/failed_scenarios.log`: List of ambiguous or skipped scenarios.

## Troubleshooting
- **OOM Errors**: If memory usage exceeds 7GB, the script will automatically reduce batch size. If it fails, reduce the `MAX_CLIPS` config in `code/config.py`.
- **Missing Dataset**: If the Orca video dataset is not found, the pipeline will attempt to use a verified synthetic fallback. If no fallback is available, the project halts.
- **Physics Engine Errors**: Ensure `mujoco` or `pybullet` is installed and compatible with the CPU architecture.
