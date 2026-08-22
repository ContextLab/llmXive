# Quickstart: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Prerequisites

- Python 3.11+
- Access to Hugging Face Hub (for `pick-a-pic` and `distilbert-base-uncased`).
- GB RAM available.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-925-llmxive-follow-up-extending-lens-rethink
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Download Models**:
    ```bash
    python -m spacy download en_core_web_sm
    # The BERT model will be downloaded automatically on first run by the script
    ```

## Running the Pipeline

The pipeline is executed in three sequential stages.

### Stage 1: Feature Extraction
Computes linguistic features for all valid captions.
```bash
python code/data/features.py
```
- **Output**: `data/processed/features.csv`, `data/logs/exclusions.log`.
- **Validation**: Checks for nulls in `linguistic_uncertainty_proxy`, `syntactic_depth`.

### Stage 2: Target Calculation
Calculates the deviation score and joins with features.
```bash
python code/data/preprocess.py
```
- **Output**: `data/processed/deviation.csv`.
- **Validation**: Checks for zero variance in target (halts if found).

### Stage 3: Model Training & Analysis
Trains XGBoost, performs permutation tests, and sensitivity sweeps.
```bash
python code/models/train.py
```
- **Output**: `results/model_metrics.json`, `results/significance_results.json`.
- **Duration**: ~2-4 hours on CPU (depending on dataset size).

## Verification

Run the test suite to ensure constitution compliance and data integrity:
```bash
pytest code/tests/
```
- **Key Test**: `test_constitution.py` ensures no image imports in `features.py` and no GPU usage in `train.py`.

## Troubleshooting

- **Error: "Missing required dataset or column: pick-a-pic/human_rating"**: The 'pick-a-pic' dataset is not available via the standard Hugging Face loader. Check your HF token or network. No synthetic data is generated.
- **Error: "Target not learnable: zero variance detected"**: All deviation scores are identical. This implies the dataset has no variance in the gap, or normalization failed.
- **Memory Error**: If OOM occurs, reduce the batch size in `code/utils/config.py` or stream the dataset more aggressively.