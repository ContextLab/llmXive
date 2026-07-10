# Quickstart: Predicting Plant Root System Architecture from Genomic Data

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- (Optional) `git` for cloning the repository

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-410-predicting-plant-root-system-architectur
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify Environment**:
    ```bash
    python -c "import sklearn; import pandas; print('Environment OK')"
    ```

## Running the Pipeline

### Option A: Full Pipeline (Mock Data Mode)
*Use this to verify the pipeline runs within CI constraints without requiring real data downloads.*

```bash
# Generate synthetic data, preprocess, train, and evaluate
python code/main.py --mode mock
```

### Option B: Real Data Mode (If Data Available)
*Requires real data files in `data/raw/`.*

```bash
# 1. Download (if URLs are configured in config.py)
python code/download.py

# 2. Preprocess
python code/preprocess.py

# 3. Train & Evaluate
python code/train.py
python code/evaluate.py

# 4. Visualize
python code/visualize.py
```

## Expected Outputs

- `data/processed/unified_dataset.parquet`: The harmonized dataset.
- `data/processed/model_metrics.csv`: R², MAE, and p-values for all models.
- `data/processed/feature_importance.csv`: Ranked markers.
- `data/processed/figures/`: SHAP plots and scatter plots.

## Troubleshooting

- **Memory Error**: If `MemoryError` occurs, the pipeline should automatically trigger PCA reduction. If not, reduce `config.MAX_FEATURES` in `code/config.py`.
- **Missing Data**: The pipeline logs excluded accessions. If >90% are excluded, check `accession_id` formatting in `data/raw/`.
- **No Verified Source**: If the pipeline reports "No verified source found" for real data, it defaults to Mock Mode.
