# Quickstart Guide: Climate-Smart Agricultural Practices & Food Security Analysis

This guide provides step-by-step instructions to reproduce the full research pipeline
from raw data download to final plots and robustness reports.

**Project**: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods
**Target Countries**: Kenya, India, Vietnam
**Data Sources**: LSMS (World Bank), NASA POWER (Climate), FAOSTAT (Agriculture)

---

## Prerequisites

- **Python 3.11+** installed and accessible via `python` or `python3` command.
- **Git** (optional, for cloning the repository).
- **Internet connection** (required for downloading raw data).
- **Disk Space**: ~10–15 GB (for raw and processed data).
- **RAM**: Minimum 8 GB (16 GB recommended for full dataset processing).

---

## 1. Environment Setup

### 1.1. Clone/Navigate to Project
```bash
cd PROJ-020-the-use-of-climate-smart-agricultural-pr
```

### 1.2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 1.3. Install Dependencies
Install all required Python packages defined in `code/requirements.txt`:
```bash
pip install --upgrade pip
pip install -r code/requirements.txt
```

### 1.4. Configure Environment Variables (Optional)
Create a `.env` file in the project root (optional, for custom paths or limits):
```bash
#.env
TARGET_COUNTRIES=KEN,IND,VNM
TARGET_YEARS=2020,2021,2022
MAX_RAM_GB=16
```
The `code/utils/config.py` module reads these variables. If not set, defaults apply.

---

## 2. Directory Structure Initialization

The pipeline expects a specific directory structure for raw data, processed data, and state files.

Run the setup script:
```bash
python code/data/setup_directories.py
```

**Expected Output**:
- `data/raw/` (for downloaded source files)
- `data/processed/` (for merged, cleaned, and sampled data)
- `state/` (for logs, checksums, and provenance)
- `figures/` (for output plots)

---

## 3. Data Ingestion Pipeline (Download & Clean)

This step downloads raw data from external sources, merges them, handles missing values, and creates a stratified sample.

### 3.1. Run the Full Data Pipeline
Execute the main data orchestration script:
```bash
python code/main.py
```

**What this does**:
1. **Downloads**:
 - **LSMS**: Household survey data for Kenya, India, Vietnam (via World Bank API or direct links).
 - **NASA POWER**: Climate data (precipitation, temperature) matched to survey coordinates.
 - **FAOSTAT**: Agricultural indicators (crop yields, fertilizer use).
2. **Cleans & Merges**:
 - Merges datasets on `country_code` + `year`.
 - Matches climate data to survey points within a **50km radius** (Haversine formula).
 - Applies imputation for missing predictor values.
3. **Samples**:
 - Ensures **N ≥ 5000 households per country** via stratified sampling (Country, Year, Region).
 - Applies Inverse Probability Weighting (IPW).
4. **Outputs**:
 - `data/processed/merged_sample.parquet` (Analysis-ready dataset).
 - `state/provenance_log.json` (Mapping of derived variables to source IDs).
 - `state/sampling_report.json` (Sample sizes and weights).

**Note**: If the raw dataset exceeds 7GB, the script automatically applies sampling to stay within memory limits.

---

## 4. Feature Engineering & CSA Index Construction

Constructs the composite Climate-Smart Agriculture (CSA) Index.

Run the feature engineering script:
```bash
python code/data/features.py
```

**What this does**:
- Calculates components: Conservation Tillage, Crop Diversification, Irrigation Efficiency, Digital Access, Finance Access.
- Normalizes components to a 0–1 scale.
- Computes the weighted composite CSA Index using IPW weights.
- Outputs: `data/processed/csa_index_features.parquet`.

---

## 5. Statistical Modeling & Analysis

Fits Mixed-Effects Regression models and performs diagnostics.

### 5.1. Run the Analysis Pipeline
```bash
python code/analysis/model.py
```

**What this does**:
- **Diagnostics**: Calculates VIF for all predictors; flags VIF > 5.0.
- **Model Fitting**: Runs Mixed-Effects models with:
 - Fixed effects: CSA Index, Digital Access, Finance Access, Controls.
 - Random effects: Country/Region intercepts.
 - Interaction terms: Digital/Finance × CSA Index.
- **Mediation Analysis**: Baron & Kenny approach for digital/finance mediation.
- **Correction**: Applies Bonferroni correction for multiple hypotheses.
- **Robustness**:
 - Sweeps CSA adoption thresholds.
 - Runs leave-one-region-out cross-validation.
 - Bootstrap resampling (1000 iterations).
- **Outputs**:
 - `data/processed/model_results.json` (Coefficients, p-values, VIFs).
 - `data/processed/robustness_report.json` (Stability metrics).
 - `state/model_provenance.log`.

---

## 6. Visualization & Reporting

Generates publication-ready plots and summary reports.

### 6.1. Run the Visualization Pipeline
```bash
python code/viz/plots.py
```

**What this does**:
- **Scatter Plots**: CSA Index vs. Food Security (with regression line).
- **Coefficient Plots**: Standardized coefficients with 95% CIs.
- **Regional Maps**: Spatial distribution of CSA adoption (using `geopandas`).
- **Distribution Plots**: Histograms of key variables.
- **Outputs**:
 - `figures/scatter_csa_vs_foodsec.png`
 - `figures/coefficient_plot.png`
 - `figures/regional_csa_map.png`
 - `figures/distribution_plots.png`
 - `state/viz_report.json`

---

## 7. Validation & Reproducibility Check

Verify that the pipeline ran successfully and all outputs are valid.

### 7.1. Run the Quickstart Validator
```bash
python code/validation/quickstart_validator.py
```

**Checks**:
- Existence of `data/processed/merged_sample.parquet`.
- Schema compliance of processed data.
- Presence of all required plot files in `figures/`.
- Validity of model results (non-empty coefficients, no NaNs in key fields).

**Expected Output**:
```
[VALID] Data file exists and schema is valid.
[VALID] Model results contain non-null coefficients.
[VALID] All 4 plot types generated.
[PASS] Pipeline validation successful.
```

---

## Troubleshooting

### "No module named 'analysis.model'"
Ensure you are running from the project root and `code/` is in `PYTHONPATH`.
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

### "Connection Timeout: LSMS API"
Check your internet connection. The pipeline requires access to World Bank and NASA POWER APIs.

### "Memory Error during Model Fitting"
- Ensure `MAX_RAM_GB` in `code/utils/config.py` is set correctly.
- The pipeline should auto-sample if raw data > 7GB. If not, reduce `TARGET_YEARS` in `.env`.

### "Missing Climate Data for Coordinates"
The pipeline uses nearest-neighbor interpolation for gaps ≤ 3 months. If gaps are larger, those rows are flagged in `state/imputation_report.json`.

---

## Citation & Provenance

All derived variables are logged in `state/provenance_log.json`.
- **LSMS Data**: World Bank Living Standards Measurement Study.
- **Climate Data**: NASA POWER Project (SSRN).
- **FAOSTAT**: Food and Agriculture Organization of the United Nations.

**Generated on**: [Timestamp from `state/provenance_log.json`]

---

## Next Steps

- **Interpret Results**: Review `data/processed/model_results.json` for associational findings.
- **Extend Analysis**: Modify `code/analysis/robustness.py` to test alternative specifications.
- **Publish**: Use `figures/` assets for reports or presentations.

**End of Quickstart Guide**