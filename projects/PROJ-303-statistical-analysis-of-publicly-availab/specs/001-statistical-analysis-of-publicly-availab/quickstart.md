# Quickstart: Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

## 1. Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to HuggingFace (no token required for public datasets)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd <repo>/specs/001-extreme-weather-spatial-analysis

# Install dependencies
pip install -r requirements.txt
```

**Key Dependencies**:
- `pandas`, `numpy`: Data manipulation.
- `scipy`, `scikit-learn`: Statistical modeling.
- `matplotlib`, `seaborn`: Visualization.
- `datasets`: HuggingFace dataset loading.
- `rpy2`: (Optional) For R-based spatial models if needed.

## 3. Data Preparation

The pipeline automatically downloads the verified dataset and performs a **Data Availability Check**.

```bash
# Run the ingestion script to fetch and preprocess data
python src/pipeline/run_analysis.py --step ingest
```

This will:
1. Download `NOAA_GHCN_Daily` from the verified HuggingFace URL.
2. Verify the date range (2000-2020). **HALT** if incomplete.
3. Filter for the Northeast USA (if applicable) or the full dataset.
4. Calculate the 95th percentile threshold for 2000–2015.
5. Generate `data/processed/extremes.csv`.

## 4. Running the Analysis

Execute the full pipeline (Ingestion -> Modeling -> Evaluation -> Visualization):

```bash
python src/pipeline/run_analysis.py --full
```

**Expected Output**:
- `outputs/metrics.json`: Brier scores, RMSE, and coverage.
- `outputs/plots/`: Variograms, QQ-plots, and regional maps.
- `logs/pipeline.log`: Execution time, fallback warnings, and data validation results.

## 5. Verification

Verify the results match the expected schema:

```bash
pytest tests/contract/test_output_schema.py
```

Check for the fallback mechanism:
- If the spatial model timed out, `logs/pipeline.log` should contain "FALLBACK: CONVERGENCE_ERROR" or "FALLBACK: TIMEOUT".

## 6. Troubleshooting

- **Memory Error**: Reduce the number of stations or subsample the time series in `src/pipeline/config.py`.
- **Convergence Failure**: Check `logs/pipeline.log` for "convergence_status: failed". The system will automatically fall back to GPD.
- **Data Not Found**: Ensure the HuggingFace URL in `src/data/loaders.py` matches the "Verified datasets" block. If the date range is incomplete, the pipeline will halt with `DATA_INCOMPLETE`.
- **Reference Validation**: If the pipeline halts at Phase 0.1, check `logs/validation.log` for citation verification errors.