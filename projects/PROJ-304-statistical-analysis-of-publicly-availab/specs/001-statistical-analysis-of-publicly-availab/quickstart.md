# Quickstart: Statistical Analysis of Urban Noise Pollution

## Prerequisites
*   Python 3.11+
*   `pip` or `conda`
*   GitHub Actions Runner (for CI execution)

## 1. Installation
Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies**:
*   `pandas`, `numpy`, `geopandas`
*   `pysal`, `libpysal`
*   `scikit-learn`
*   `statsmodels`
*   `linearmodels`
*   `pyarrow`

## 2. Data Preparation
Since no verified geospatial dataset is provided in the prompt, the pipeline includes a **synthetic data generator**.

```bash
# Generate synthetic data (a substantial number of grid cells)
python code/synthetic_data.py
```
This creates `data/processed/harmonized.parquet`.

*Note: If you have real data (CSV/GeoJSON), place it in `data/raw/` and modify `code/ingestion.py` to point to your files.*

## 3. Running the Pipeline
Execute the full analysis pipeline:

```bash
python code/main.py
```

**What happens**:
1.  **Ingestion**: Loads data, harmonizes to 200m grid.
2.  **Preprocessing**: Applies IQR filter, handles missing values, aggregates **per day** (by `grid_id` and `date`).
3.  **Modeling**: Fits OLS, Spatial Lag, and Spatial Error models using **Conley/Cluster-Robust SEs**.
4.  **Validation**: Runs 5-fold spatial CV and permutation tests.
5.  **Reporting**: Saves results to `data/processed/`.

## 4. Verifying Results
Check the output files:
*   `data/processed/model_results.json`: Contains coefficients, AIC, R², Moran's I.
*   `data/processed/cv_results.json`: Contains cross-validation metrics.
*   `data/processed/report.md`: Human-readable summary of findings.

**Success Criteria Check**:
*   **SC-001**: Verify `moran_i_residual` for spatial models is ≤ 0.1 and reduced by >10% vs OLS. (Note: If synthetic data has no spatial dependence, this may not be met, which is a valid result).
*   **SC-002**: Verify permutation test p-value < 0.05 for RMSE difference.
*   **SC-005**: Check that ≥30% of predictors are significant after BH-FDR.

## 5. Troubleshooting
*   **Memory Error**: If running out of RAM, reduce `NUM_GRID_CELLS` in `code/config.py`.
*   **Convergence Failure**: If Spatial models fail, the pipeline logs a warning and falls back to OLS. Check `logs/pipeline.log`.
*   **CRS Mismatch**: Ensure all input data is in WGS84 (EPSG:4326).
*   **Weight Matrix Failure**: If both Queen and KNN matrices fail, the pipeline will halt with a CRITICAL error.
