# Quickstart: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Prerequisites

- Python 3.11+
- `pip`
- 7GB+ RAM (for local testing; CI will handle streaming).

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-925-llmxive-follow-up-extending-lens-rethink
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download Dependencies**
   ```bash
   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

## Running the Pipeline

The pipeline is executed in four stages via the `code/main.py` entry point (or individual scripts).

### Step 0: Data Preprocessing (Generate Scores)
Generates `clip_score` and `human_rating` if missing.
```bash
python code/data/scores.py --input data/raw/pick-a-pic.jsonl --output data/processed/scores.jsonl
```
- **Note**: If `pick-a-pic` is unavailable, this step will fail with `DataSchemaError`.

### Step 1: Feature Extraction
Extracts linguistic features from captions.
```bash
python code/data/features.py --input data/processed/scores.jsonl --output data/processed/features.csv
```
- **Note**: If the uncertainty proxy fails validation (correlation < 0.3), this step will halt.

### Step 2: Target Calculation & Validation
Calculates deviation scores and checks for zero variance.
```bash
python code/data/preprocess.py --features data/processed/features.csv --output data/processed/deviation.csv
```
- **Check**: Ensure `deviation.csv` is created and `is_learnable` is True.

### Step 3: Training & Evaluation
Trains the XGBoost model and runs statistical tests.
```bash
python code/data/train.py --features data/processed/features.csv --target data/processed/deviation.csv --output results/
```
- **Output**: `results/stability_metrics.json`, `results/model.json`, `results/logs.txt`.

## Verification

Run the test suite to verify constitution compliance and schema validity:
```bash
pytest code/tests/
```

## Troubleshooting

- **"Target not learnable"**: The dataset has zero variance in deviation scores. Check data integrity.
- **"Missing required dataset"**: The `pick-a-pic` dataset is not accessible. Verify network or HF credentials.
- **"Invalid Proxy"**: The uncertainty proxy failed validation (correlation < 0.3). The study cannot proceed.
- **Memory Error**: Reduce batch size in `features.py` or use streaming mode.
