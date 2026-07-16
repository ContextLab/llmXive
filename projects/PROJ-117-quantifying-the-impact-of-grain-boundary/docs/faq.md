# Frequently Asked Questions

## General Questions

### What is the goal of this project?
To quantify the relationship between grain boundary character (misorientation, boundary plane, Σ value) and atomic diffusivity using machine learning on atomistic simulation data.

### Why is n ≥ 500 required?
This minimum ensures sufficient data for reliable statistical validation, k-fold cross-validation, and meaningful feature importance analysis. It aligns with community standards for materials property prediction.

### Can I use GPU acceleration?
No. The pipeline is designed for CPU-only execution to comply with GitHub Actions free-tier constraints (2 cores, limited RAM).

## Data Questions

### Where does the data come from?
- Materials Project (via API)
- OpenKIM (via API)
- NIST (via API or file download)

### What if I don't have API keys?
You must obtain API keys from Materials Project and OpenKIM. Without valid keys, the download step will fail.

### Can I use my own dataset?
Yes, but it must conform to the schema in `docs/data_schema.md` and contain at least 500 valid records with all required features.

## Model Questions

### Why XGBoost?
XGBoost provides strong performance on tabular data, handles feature interactions well, and has excellent SHAP integration for interpretability.

### What if my model doesn't achieve R² ≥ 0.7?
The pipeline will still complete, but the sensitivity analysis will report a lower pass rate. Consider:
- Feature engineering improvements
- Hyperparameter tuning adjustments
- Collecting more data

### How is hyperparameter tuning performed?
Using RandomizedSearchCV with 5-fold cross-validation on the training set.

## Error Questions

### What does "Data Insufficiency" mean?
Fewer than 500 valid records remain after preprocessing. Check your API keys, search keywords, and data quality.

### Why did my script exit with code 1?
Code 1 indicates a data insufficiency error. Check the log message for details on missing features or record counts.

## Performance Questions

### How long does the pipeline take?
Target: <6 hours on 2 CPU cores with <7GB RAM. Actual time depends on dataset size and API response times.

### Can I run steps in parallel?
Only tasks marked [P] in `tasks.md` can run in parallel. The main pipeline (T009→T021) is sequential.

### How can I optimize performance?
- Use vectorized operations (already implemented in `optimization_utils.py`)
- Ensure sufficient RAM
- Use fast storage (SSD)

## Testing Questions

### How do I run tests?
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### What if tests fail?
Check the error message, verify dependencies are installed, and ensure the pipeline has been run successfully before testing.

## Documentation Questions

### Where can I find the API reference?
See `docs/api_reference.md` for detailed module documentation.

### How do I understand the data schema?
See `docs/data_schema.md` for complete schema definitions.

### Where is the threshold justification?
See `docs/threshold_justification.md` for the R² ≥ 0.7 rationale.

## Advanced Questions

### Can I add new features?
Yes, but you must:
1. Update the data schema
2. Modify the preprocessing step
3. Re-train the model
4. Validate the change

### How do I deploy the model?
The model is saved as `models/best_model.json`. You can load it using:
```python
import json
import xgboost as xgb
with open('models/best_model.json', 'r') as f:
 model = xgb.XGBRegressor()
 model.load_model(f)
```

### Can I use this for other materials?
The pipeline is designed for grain boundary diffusivity but can be adapted for other materials properties with appropriate data and feature engineering.
