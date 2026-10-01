# Project Plan: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

## 0. Project Overview

### 0.1 Objective
To investigate the relationship between environmental conditions (temperature, humidity, precipitation) and the visual severity of plant diseases, using publicly available image datasets and weather records. This is an **observational study**; no expert-labeled ground truth severity scores exist.

### 0.2 Scope
- **Data Sources**: PlantVillage dataset (images), Open-Meteo API / NOAA GHCN-Daily API (weather).
- **Methodology**: Extract visual features (lesion area, color, texture) from images; link to 7-day historical weather; train machine learning models to predict severity residuals; perform permutation tests to validate environmental modulation.
- **Constraints**: CPU-only execution (RAM < 7GB), no synthetic data fallbacks, strict reproducibility.

### 0.3 Key Assumptions
- PlantVillage images contain metadata (location/date) in filenames or sidecar files.
- Open-Meteo API provides sufficient granularity for 7-day weather aggregation.
- Visual features (lesion area ratio, necrosis color index) are proxies for disease severity.
- **No ground truth exists**: The study measures associational links, not causal validation against expert scores.

## 1. Data Pipeline Strategy

### 1.1 Data Acquisition
- **Images**: Download PlantVillage dataset using `datasets` library with **streaming** enabled to avoid memory overflow.
- **Weather**: Query Open-Meteo API for 7-day historical data (temperature, humidity, precipitation).
- **Fallback**: If Open-Meteo fails, query NOAA GHCN-Daily API for the nearest station. If both fail, **exclude the record** (no imputation, no synthetic data).

### 1.2 Preprocessing
- **Image Processing**: Use OpenCV to extract:
 - Lesion Area Ratio (pixel count of disease vs. total leaf area)
 - Necrosis Color Index (ratio of brown/black pixels)
 - Texture Entropy (GLCM-based complexity)
- **Weather Aggregation**: Compute 7-day rolling means/sums for temperature, humidity, and precipitation.

### 1.3 Data Integration
- Merge image features and weather data into a single `unified_analysis.csv`.
- **Validation**: Assert non-null values for all feature columns. Log warnings for excluded records.

## 2. Modeling Strategy

### 2.1 Baseline Model
- Train a Random Forest (RF) on image features alone to predict severity.
- Generate Out-of-Fold (OOF) predictions to calculate residuals (Actual - Predicted).

### 2.2 Augmented Model
- Train a second RF on **weather variables + interaction terms** to predict the **calibrated residuals** from the baseline model.
- This tests the hypothesis: "Weather conditions modulate the severity unexplained by visual features alone."

### 2.3 Hypothesis Validation
- **Paired Permutation Test**: Shuffle weather features in the training set 1000 times to generate a null distribution of R² scores.
- Calculate p-value: `(count(null_R2_diff >= observed_R2_diff) + 1) / 1001`.
- **Null Result Flag**: If p-value >= 0.05, explicitly flag "Null Result" in `results.json`.

## 3. Visualization & Sensitivity

### 3.1 Partial Dependence Plots
- Generate plots showing the interaction effect of humidity/temperature on predicted residual severity.

### 3.2 Sensitivity Analysis
- Sweep classification thresholds at absolute deviations {0.01, 0.05, 0.1} from the 90th percentile baseline.
- Report F1 scores and False Positive Rates for each threshold.

## 4. Configuration & Reproducibility

### 4.1 Configuration File
- All paths, seeds, API keys, and constants are defined in `code/config.py`.
- **Fixed Parameters**: The **7-day weather window is a fixed parameter** defined in `config.py` (e.g., `WEATHER_WINDOW_DAYS = 7`). It is **not dynamically adjusted** based on data availability or record characteristics. This ensures consistent aggregation across all records.

### 4.2 State Management
- SHA-256 hashes of all artifacts are stored in `state/*.yaml`.
- Any change to input data or code triggers a state update and re-validation.

## 5. Execution & Resource Limits

### 5.1 Memory Constraints
- **RAM Limit**: 7GB.
- **Strategy**: Use streaming for dataset loading; process images in batches; use memory-mapped arrays where possible.

### 5.2 Runtime Limits
- **Max Runtime**: 6 hours.
- **Strategy**: Optimize feature extraction; limit permutation test iterations if necessary (min 1000).

### 5.3 Monitoring
- Log RAM peak and runtime to `logs/resource_usage.log`.
- Fail execution if limits are exceeded.

## 6. Risk Mitigation

### 6.1 Data Gaps
- If weather API fails for a record, exclude the record (log warning). Do not impute.
- If PlantVillage metadata is missing, exclude the record.

### 6.2 Model Failure
- If baseline RF fails to converge, log error and halt.
- If permutation test p-value is undefined, flag as "Null Result".

### 6.3 Reproducibility
- All random seeds are fixed in `config.py`.
- Deterministic algorithms are preferred (e.g., `n_jobs=1` for RF if parallelism causes instability).

## 7. Deliverables

- `data/processed/unified_analysis.csv`: Merged image and weather features.
- `artifacts/results.json`: Model metrics, p-values, sensitivity data.
- `figures/pdp_humidity.png`, `figures/pdp_temp.png`: Partial dependence plots.
- `state/projects/PROJ-405-*.yaml`: Artifact hashes and state.
- `quickstart.md`: Reproduction instructions.

## 8. Timeline

- **Phase 1**: Setup & Plan Correction (T047-T050)
- **Phase 2**: User Story 1 (Data Pipeline)
- **Phase 3**: User Story 2 (Modeling)
- **Phase 4**: User Story 3 (Visualization)
- **Phase 5**: Validation & Reporting