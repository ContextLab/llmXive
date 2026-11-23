# Quickstart: VLM Proxy Dimension Mimicry & Bias Characterization

## Prerequisites
- Python 3.11+
- Access to a GitHub Actions runner (or local machine with sufficient RAM).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-899-llmxive-follow-up-extending-evalverse-pi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for reproducibility.*

## Running the Pipeline

### Full Pipeline (CPU-Only)
Run the entire analysis (extraction, correlation, baselines, sensitivity) on the verified datasets:
```bash
python src/cli/run_pipeline.py --seed 42 --output-dir data/processed
```

### Profiling Only
Run only the memory/time profiling on a subset of clips (e.g., first 100):
```bash
python src/cli/run_pipeline.py --seed 42 --profile-only --sample-size 100
```

### Validation
Run the contract tests to ensure output schemas are correct:
```bash
pytest tests/contract/
```

## Expected Outputs
After a successful run, the following files will be in `data/processed/`:
- `correlations.csv`
- `baseline_predictions.csv`
- `permutation_raw.csv`
- `max_t_stats.csv`
- `permutation_results.csv`
- `dimension_viability.csv`
- `profiling_logs.json`
- `batch_raw_logs.json`
- `sensitivity_matrix.json`
- `scaling_projection.json`
- `power_analysis.json`

## Troubleshooting
- **OOM Error**: Ensure `streaming=True` is not disabled. The pipeline must not load the full dataset.
- **Missing URL**: If a video URL in the dataset is broken, the clip is skipped. Check `data/processed/skipped_clips.log`.
- **Constraint Violation**: If the pipeline reports "Constraint Violation", the current hardware exceeds the 7GB/6h limit.
- **Proxy Mismatch**: If the pipeline reports "PROXY_MISMATCH", the dataset dimensions do not match the expected action-based scores.
- **Underpowered**: If `power_analysis.json` reports "underpowered", the sample size is insufficient to detect the target correlation.