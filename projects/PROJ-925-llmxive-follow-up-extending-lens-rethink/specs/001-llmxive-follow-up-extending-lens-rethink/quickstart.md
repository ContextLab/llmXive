# Quickstart: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Prerequisites
- Python 3.11+
- Git
- Access to Hugging Face Hub (for datasets)

## Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-925-llmxive-follow-up-extending-lens-rethink
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import torch; import xgboost; import spacy; import transformers; print('All dependencies OK')"
   ```

3. **Download Data**
   The pipeline will automatically download the dataset on first run if not present in `data/raw`.
   - Ensure you have sufficient disk space for the raw dataset.
   - **Note**: If 'pick-a-pic' is used, the run will be limited to N=1000 samples for on-the-fly CLIP inference. If no verified dataset is found, the pipeline will halt with an error.

## Running the Pipeline

### 1. Feature Extraction
Extract linguistic features from the dataset.
```bash
python code/data/features.py --input data/raw/pick-a-pic.jsonl --output data/processed/features.csv
```
- **Expected Output**: `data/processed/features.csv` with columns: `caption_id`, `linguistic_uncertainty_proxy`, `syntactic_depth`, `visual_token_density`, etc.

### 2. Target Calculation
Compute the alignment deviation scores.
```bash
python code/data/preprocess.py --features data/processed/features.csv --input data/raw/pick-a-pic.jsonl --output data/processed/deviation.csv
```
- **Expected Output**: `data/processed/deviation.csv` with `deviation_score`.

### 3. Model Training & Evaluation
Train the XGBoost model and run permutation tests.
```bash
python code/models/train.py --features data/processed/features.csv --target data/processed/deviation.csv --output results/
```
- **Expected Output**:
  - `results/model.pkl` (trained model)
  - `results/feature_importance.json`
  - `results/stability_metrics.json`
  - `results/significance_results.csv`
  - `results/memory_profile.json` (Peak RSS via `tracemalloc`)
  - `results/timing_profile.json` (Wall-clock time via `time`)

## Verification
Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```
- Check that `tests/contract/test_schemas.py` passes (validates YAML schemas).
- Check that `tests/integration/test_pipeline.py` passes (end-to-end run).

## Troubleshooting
- **OOM Error**: If you encounter MemoryError, reduce the batch size in `code/data/features.py` or enable streaming (default).
- **Missing Data**: If 'pick-a-pic' cannot be downloaded, the script will raise `DataSchemaError`. Check internet connection or Hugging Face token. **The pipeline will not proceed with synthetic data.**
- **CPU Slowness**: Ensure `torch.set_num_threads(1)` is set (done automatically in `train.py`).
- **Versioning**: The `main.py` script automatically updates `state/projects/...yaml` with the new hash after a successful run.