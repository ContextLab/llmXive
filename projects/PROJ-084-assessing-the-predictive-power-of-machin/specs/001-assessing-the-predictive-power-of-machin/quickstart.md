# Quickstart: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to HuggingFace (no token required for public datasets)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Setup

The pipeline automatically downloads the dataset on first run. To manually verify:
1. Ensure `data/raw/` exists.
2. The script will fetch from: `https://huggingface.co/datasets/chembl/uspto-yield/resolve/main/data/train.parquet`

## Running the Pipeline

Execute the main script to run the full pipeline (Preprocessing -> Training -> Evaluation):
```bash
python code/main.py
```

### Configuration
Edit `code/config.py` to adjust:
- `RANDOM_SEED`: For reproducibility.
- `DATASET_URL`: To switch between verified USPTO Yield sources.
- `GRID_SEARCH_PARAMS`: To reduce tuning time (e.g., fewer `n_estimators`).

## Outputs

After completion, check `data/results/`:
- `metrics.json`: Overall R², RMSE, MAE.
- `per_class_metrics.json`: Performance by reaction type.
- `feature_importance.json`: Top predictive substructures (aggregated).
- `models/`: Serialized Random Forest and SVM models.

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

Run contract tests to validate data schemas:
```bash
pytest tests/contract/
```

## Troubleshooting

- **RAM Error**: Reduce `GRID_SEARCH_PARAMS` or verify the subset size in `config.py`.
- **RDKit Errors**: Ensure `rdkit` is installed via `pip install rdkit` (not `rdkit-pypi` if on Linux).
- **Dataset Missing**: Check internet connection and verify the URL in `config.py` matches the verified list.

