# Quickstart: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Prerequisites
- Python 3.11+
- 7 GB RAM available
- Internet access (for dataset download)

## 2. Installation

```bash
# Clone and enter project
cd projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download
The system automatically downloads the SoCRATES dataset on first run. To pre-fetch:

```bash
python src/data/generate_trajectories.py --download-only
```
*Output: `data/raw/socrates_prompts.parquet` (Checksum verified).*

## 4. Running the Pipeline

### Step 1: Generate Filtered Dataset
```bash
python src/data/generate_trajectories.py --oversample-high-difficulty
```
*Output: `data/processed/filtered_trajectories.jsonl`.*

### Step 2: Train State Classifier
```bash
python src/data/classifier_training.py
```
*Output: `models/state_classifier.pkl`.*

### Step 3: Run Experiments (CPU Only)
```bash
python src/experiments/runner.py --models llama-3-8b,mistral-7b --conditions adapter,static
```
*Output: `data/results/experiment_logs/`.*

### Step 4: Statistical Analysis
```bash
python src/analysis/stats_utils.py
```
*Output: `data/results/statistical_report.json`.*

## 5. Validation & Verification

### Validate Quickstart
Run the validation script to ensure end-to-end reproducibility:
```bash
python tests/integration/test_quickstart_validation.py
```
*Expected Output*: `data/results/quickstart_validation_log.txt` containing "SUCCESS".

### Verify Schemas
Ensure all output files match the contracts:
```bash
pytest tests/contract/test_schemas.py
```

## 6. Troubleshooting
- **OOM Error**: Reduce `--batch-size` in `runner.py` or exclude larger models.
- **CUDA Error**: Ensure `device="cpu"` is set in `transformers` config (enforced by script).
- **Missing Data**: Check `data/raw/` checksums against `state/...yaml`.