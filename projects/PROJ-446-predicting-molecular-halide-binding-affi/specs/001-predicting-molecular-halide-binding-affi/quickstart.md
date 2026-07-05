# Quickstart: Predicting Molecular Halide Binding Affinities with Machine Learning

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with sufficient RAM

## 1. Clone and Setup

```bash
git clone <repository-url>
cd projects/001-predicting-halide-binding-affinities
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Data Preparation

The project includes a script to download data from verified sources.

```bash
# Download raw data (or generate simulated data if sources are missing)
python code/data_ingestion.py --download
```

*Note: If the verified datasets do not contain the required binding constants, the script will automatically generate a simulated dataset using the physics-based model defined in `research.md` and log a warning.*

## 3. Run the Pipeline

Execute the full pipeline (ingestion -> modeling -> analysis):

```bash
python code/run_pipeline.py
```

This will:
1. Ingest and clean data.
2. Generate features (ECFP4, RDKit descriptors).
3. Train Random Forest and Gradient Boosting models (5-fold CV).
4. Perform statistical comparisons (Bootstrap Resampling, BH correction).
5. Generate reports and plots.

## 4. Verify Results

Check the output directory:

```bash
ls data/processed/
# Expected: filtered_dataset.csv, feature_matrix.parquet, model_results.json, report.pdf
```

Run unit tests:

```bash
pytest tests/
```

## 5. Expected Output

- **Model Performance**: R² and RMSE per halide ion with 95% Confidence Intervals.
- **Feature Importance**: Top 10 determinants of halide selectivity.
- **Statistical Report**: P-values (adjusted) for halide comparisons (if applicable).
- **Plots**: Partial Dependence Plots for key features.

## 6. Troubleshooting

- **Memory Error**: If RAM exceeds 7GB, reduce the dataset size in `code/data_ingestion.py` (sample to a large-scale dataset).
- **Data Missing**: If the pipeline falls back to simulated data, check `logs/data_ingestion.log` for the "Data Gap" warning.