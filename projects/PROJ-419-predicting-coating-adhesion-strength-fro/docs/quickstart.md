# Quickstart Guide: Predicting Coating Adhesion Strength

This guide provides step-by-step instructions to set up, run, and validate the
`llmXive` automated science pipeline for predicting coating adhesion strength from
composition and surface features.

## Prerequisites

- Python 3.11+
- pip (Python package installer)
- ~7GB RAM available (for data processing and model training)
- Internet connection (to fetch data from verified sources)

## 1. Setup Environment

Clone the repository and create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**Required packages**:
- pandas, scikit-learn, shap, requests, numpy, pyyaml, pytest, ruff, black, tomlkit, scipy

## 2. Project Structure

```
PROJ-419/
├── code/ # Core implementation modules
├── data/
│ ├── raw/ # Raw data fetched from APIs (auto-generated)
│ └── processed/ # Cleaned, aligned datasets (auto-generated)
├── docs/ # Documentation (this file, data-model.md)
├── state/ # Pipeline state and halt signals
├── tests/ # Unit and integration tests
├── requirements.txt # Dependencies
└── main.py # Orchestration entry point
```

## 3. Run the Pipeline

Execute the full pipeline from data ingestion to final report:

```bash
python code/main.py
```

The pipeline performs the following steps:
1. **Data Gap Analysis**: Verifies access to Materials Project and NIST Surface Metrology APIs.
2. **Data Ingestion**: Fetches raw data, filters by ASTM D4541, validates unique identifiers, and handles duplicates.
3. **Preprocessing**: Encodes compositional data, standardizes surface metrics, and performs construct validity checks.
4. **Modeling**: Trains Gradient Boosting and Random Forest models with nested cross-validation and SHAP analysis.
5. **Evaluation**: Compares full models against composition-only and surface-only baselines using corrected t-tests.
6. **Reporting**: Generates final JSON reports and saves processed datasets.

### Expected Outputs

After successful completion, the following files will be generated:

- `data/processed/coating_adhesion_dataset.csv`: Unified, cleaned dataset.
- `state/validation_report.json`: Metrics on exclusion ratio, success rate, and construct validity.
- `state/model_report.json`: Model performance (R², RMSE, MAE) and SHAP rankings.
- `state/evaluation_report.json`: Statistical comparison results (p-values, Bonferroni correction).
- `state/halt_signal.yaml`: Created only if safety gates fail (e.g., exclusion ratio ≥ 10%).

## 4. Validation Gates

The pipeline enforces strict safety gates to ensure data quality and statistical rigor:

- **Power Analysis**: Ensures sample size N ≥ 1,000.
- **Exclusion Ratio**: Rejects run if missing targets ≥ 10%.
- **Success Rate**: Rejects run if processing success rate < 95%.
- **Construct Validity**: Excludes derived proxies with |r| < 0.3 or R² < 0.05.
- **Halt Signal**: If data sources are unavailable, `state/HALT_SIGNAL.yaml` is written, and execution stops immediately.

## 5. Running Tests

Run unit and integration tests:

```bash
pytest tests/ -v
```

Tests cover:
- ASTM D4541 filtering logic
- Duplicate resolution strategies
- Nested cross-validation (no data leakage)
- SHAP value stability
- Statistical test implementations (Nadeau & Bengio t-test, Bonferroni correction)

## 6. Troubleshooting

### "Data Gap: Missing Verified Sources"
- Ensure internet connectivity.
- Verify Materials Project and NIST API URLs are accessible.
- Check `state/HALT_SIGNAL.yaml` for specific failure reasons.

### "Exclusion Ratio Too High"
- Review raw data sources for missing target variables.
- Adjust filtering criteria if legitimate data is being excluded.

### "Runtime > 4 Hours"
- The pipeline is optimized for < 4h runtime (SC-004).
- If exceeded, check `state/performance_report.json` for bottlenecks.
- Consider increasing RAM or reducing sample size (if justified).

## 7. Next Steps

- **Data Curation**: Improve data alignment by contributing verified identifiers to open repositories.
- **Model Extension**: Add more advanced models (e.g., XGBoost, Neural Networks) following the same pipeline structure.
- **Deployment**: Integrate the pipeline into a CI/CD workflow for automated re-training.

For detailed data schema and entity definitions, see `docs/data-model.md`.
