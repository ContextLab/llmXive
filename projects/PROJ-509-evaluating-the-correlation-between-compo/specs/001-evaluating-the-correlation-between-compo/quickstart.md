# Quickstart: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the MP-2020 dataset (via `MPDS_API_KEY` environment variable or local cache)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` is located at `projects/PROJ-509-evaluating-the-correlation-between-compo/code/requirements.txt`.*

## Running the Pipeline

The pipeline is executed via `code/main.py`.

```bash
cd code
python main.py
```

### Steps Executed
1. **Ingestion**: Downloads/loads MP-2020 dataset (via MPDS API or local cache), filters inorganic compounds, checksums data, and verifies version.
2. **Feature Engineering**: Computes mean/variance descriptors for 5 elemental properties and derives `chemical_family`.
3. **Model Training**: Trains Random Forest and Gradient Boosting models (80/20 split by Chemical Family).
4. **Evaluation**: Calculates R², MAE, RMSE; computes overfitting ratio; saves models and metrics.
5. **Analysis**: Computes feature importance (Conditional Permutation, SHAP), VIF, and generates ALE plots.
6. **Logging**: Records execution time, statistical tests, and ALE metrics to `data/evaluation/model_metrics.json` and related JSON files.

## Output Artifacts

After successful execution, the following files will be generated in `data/evaluation/`:

- `model_rf.pkl`: Trained Random Forest model.
- `model_gb.pkl`: Trained Gradient Boosting model.
- `model_metrics.json`: Performance metrics (R², MAE, RMSE, execution time, overfitting_ratio).
- `feature_ranking.json`: Ranked list of descriptors by importance.
- `permutation_importance.json`: Permutation importance scores and correlation `r`.
- `vif_scores.json`: Variance Inflation Factor scores for all features.
- `ale_metrics.json`: Non-linearity scores for top 3 features.
- `statistical_tests.json`: P-values and CIs for model comparison.
- `ale_*.png`: Accumulated Local Effects plots for the top 3 features.

## Verification

To verify the results:

1. **Check Metrics**:
   ```bash
   cat data/evaluation/model_metrics.json
   ```
   Ensure `val_r2` > 0.0 and `execution_time` < 6 hours.

2. **Check Feature Ranking**:
   ```bash
   cat data/evaluation/feature_ranking.json
   ```
   Ensure top 5 features are listed.

3. **Check ALE Plots**:
   Verify `data/evaluation/ale_*.png` files exist and are non-empty. Check `ale_metrics.json` for non-linearity scores > 0.5.

4. **Run Tests**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

- **Dataset Download Failed**: Ensure `MPDS_API_KEY` is set in environment variables, or that `data/raw/mp-2020.csv` exists and is checksummed.
- **Memory Error**: The dataset is small. If this occurs, check for memory leaks or incorrect data loading.
- **Overfitting Flag**: If `overfitting_ratio` is high, review the stratification strategy or model hyperparameters.
