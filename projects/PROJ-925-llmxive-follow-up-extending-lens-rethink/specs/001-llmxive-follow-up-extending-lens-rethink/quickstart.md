# Quickstart: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Sufficient disk space for dependencies and cached models.

## Installation

1. **Clone and Setup**
   ```bash
   cd projects/PROJ-925-llmxive-follow-up-extending-lens-rethink
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import spacy; import xgboost; import transformers; print('All dependencies OK')"
   ```

## Running the Pipeline

The pipeline is executed via a single orchestration script or individual steps.

### Step 1: Download & Preprocess (Streaming)
Downloads a sample of COCO data and computes CLIP scores.
```bash
python code/data/download.py --sample-size sufficient to ensure statistical power for detecting the target effect size. --streaming
python code/data/preprocess.py --input data/raw/coco_stream.parquet --output data/processed/caption_records.csv
```

### Step 2: Feature Extraction
Computes linguistic features on CPU.
```bash
python code/data/features.py --input data/processed/caption_records.csv --output data/processed/features.csv --batch-size
```

### Step 3: Training & Significance Testing
Trains the XGBoost model and performs permutation tests.
```bash
python code/data/train.py --features data/processed/features.csv --target deviation_score --output results/model_artifacts/
```

## Verification

Run the unit tests to ensure feature extraction logic is correct:
```bash
pytest code/tests/test_features.py -v
pytest code/tests/test_train.py -v
```

## Expected Outputs

- `data/processed/features.csv`: Contains `semantic_entropy`, `syntactic_depth`, etc.
- `results/model_artifacts/xgboost_model.json`: The trained model.
- `results/model_artifacts/significance.json`: Feature rankings with p-values.
- `results/plots/feature_importance.png`: Visualization of top predictors.
