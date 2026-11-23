# Project Plan: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

## Overview
This project aims to analyze the relationship between visual disease severity indicators in plant leaves and historical weather conditions. The study is observational, utilizing publicly available image datasets (PlantVillage) and meteorological data APIs (Open-Meteo, NOAA GHCN-Daily).

## Objectives
1. Construct a unified dataset linking plant disease images to local weather history.
2. Validate the hypothesis that environmental conditions modulate disease severity residuals.
3. Visualize interaction effects and perform sensitivity analysis on classification thresholds.

## Workflow Steps

### Step 0: Project Setup & Configuration
0.1. Initialize Python environment with required dependencies (opencv, scikit-learn, pandas, etc.).
0.2. Configure logging and state management.
0.3. Define configuration constants in `code/config.py`.
0.4. **Data Verification Strategy**: Verify non-null values for image features and weather variables. **Study is observational; no ground truth exists.** We do not use expert-labeled severity scores or simulated ground truth.
0.5. Define the 7-day weather aggregation window as a **fixed parameter** in `config.py` (e.g., `WEATHER_WINDOW_DAYS = 7`). This window is NOT dynamically adjusted based on data availability or other factors.

### Step 1: Data Ingestion & Feature Extraction
1.1. Download PlantVillage dataset using `datasets.load_dataset(..., streaming=True)` to manage memory constraints.
1.2. Extract visual features (lesion area ratio, necrosis color index, texture entropy) using OpenCV.
1.3. Fetch historical weather data via Open-Meteo API. **Fallback**: If Open-Meteo fails, query NOAA GHCN-Daily API for the nearest station. If both fail, exclude the record. **No local CSVs** are used as data sources.
1.4. Merge image features and weather data into a unified analysis table (`data/processed/unified_analysis.csv`).
1.5. Exclude records with missing location metadata (latitude/longitude) or non-null feature values.

### Step 2: Modeling & Hypothesis Validation
2.1. Train a baseline Random Forest model to predict disease severity from image features alone.
2.2. Generate Out-of-Fold (OOF) predictions and calculate raw residuals (Actual - Predicted).
2.3. Calibrate residuals using isotonic regression or mean-centering.
2.4. Train an augmented Random Forest model to predict calibrated residuals using weather variables and interaction terms.
2.5. Perform a paired permutation test to validate the hypothesis:
 - Shuffle weather feature columns in the training set.
 - Retrain models and compute the distribution of R² differences.
 - Calculate the p-value for the observed R² difference.
2.6. Record results (R², MAE, p-value) in `artifacts/results.json`.

### Step 3: Visualization & Sensitivity Analysis
3.1. Generate Partial Dependence Plots (PDP) for interaction effects between humidity/temperature and image features.
3.2. Perform sensitivity analysis by sweeping classification thresholds (absolute deviations from 90th percentile baseline).
3.3. Calculate F1 scores and False Positive Rates for swept thresholds.
3.4. Generate final visualization report and append to `results.json`.

### Step 4: Validation & Reporting
4.1. Verify all metrics against acceptance criteria.
4.2. Compute SHA-256 hashes for key artifacts (`results.json`, `unified_analysis.csv`).
4.3. Update state file (`state/projects/PROJ-405.yaml`) with hashes and timestamps.
4.4. Generate `quickstart.md` with exact commands, paths, and seed values.
4.5. Log resource usage (RAM peak, runtime) and verify constraints (<7GB RAM, <6h runtime).

## Constraints
- **Memory**: All operations must fit within 7GB RAM. Use streaming and batch processing where necessary.
- **Data**: No synthetic data fallbacks. If real data fetch fails, the script must fail loudly.
- **Ground Truth**: No expert-labeled severity scores are used. The study is purely associational.
- **Weather Window**: The 7-day aggregation window is a fixed parameter, not dynamic.

## Dependencies
- `opencv-python`
- `scikit-learn`
- `pandas`
- `numpy`
- `requests`
- `datasets`
- `matplotlib`
- `seaborn`
- `pyyaml`
- `pytest`