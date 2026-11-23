# Quickstart: Predicting the Impact of Composition on the Density of Metallic Glasses

## Prerequisites
- Python 3.10+
- pip / virtualenv
- Git

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd projects/PROJ-461-predicting-the-impact-of-composition-on-/
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `lightgbm`, `mendeleev`, `shap`, `pandas`, `numpy`, `scikit-learn`.*

## Running the Pipeline

### Standard Mode (Real Data)
Attempts to download from Zenodo/Materials Cloud. If successful, trains on real data.
```bash
python code/main.py --mode standard
```
-   **Output**: `data/clean_data.csv`, `models/model.pkl`, `reports/analysis_report.html`
-   **Logs**: Check `logs/pipeline.log` for download status.

### Validation Mode (Synthetic Data)
Forces the generation of synthetic data if real data is unavailable or <50 rows.
```bash
python code/main.py --mode validation
```
-   **Output**: `data/synthetic_data.csv`, `models/model.pkl`, `reports/analysis_report.html`
-   **Logs**: Will contain warning `E_DATA_INSUFFICIENT` if triggered.

### Running Tests
```bash
pytest tests/ -v
```
-   Includes contract tests against `contracts/` schemas.
-   Includes unit tests for feature engineering formulas.

## Output Artifacts

| Artifact | Location | Description |
| :--- | :--- | :--- |
| Raw Data | `data/raw_data.csv` | Downloaded dataset (if available) |
| Clean Data | `data/clean_data.csv` | Preprocessed, normalized dataset |
| Model | `models/model.pkl` | Trained LightGBM regressor |
| Report | `reports/analysis_report.html` | Interactive HTML report with plots |

## Troubleshooting

-   **Download Failed**: If Zenodo/Materials Cloud are unreachable, the system automatically switches to `validation` mode. Check logs for `E_DATA_INSUFFICIENT`.
-   **Missing Elements**: If an element in the dataset is not in `mendeleev`, the row is logged and excluded.
-   **Memory Error**: If the dataset is too large, ensure the `streaming` flag is used (if implemented) or reduce the synthetic sample size in `code/data/download.py`.
