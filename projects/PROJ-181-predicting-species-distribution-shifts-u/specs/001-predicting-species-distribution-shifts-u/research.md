# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Statement & Research Questions

**Primary Question**: Can historical Species Distribution Models (SDMs) trained on 1970‑2000 data accurately predict species distributions in 2005‑2020 under changing climate conditions, and how does model performance degrade when projected to the 2050 SSP2‑4.5 scenario?

**Secondary Questions**  
1. Which SDM algorithm (Random Forest, Bioclim, **Regularized Logistic Regression (Presence-Background)**) demonstrates the highest robustness to temporal non‑stationarity?  
2. How does spatial thinning (10 km) and bias‑corrected background sampling impact model performance?  
3. Are performance differences between algorithms statistically significant after correcting for multiple comparisons?

## 2. Dataset Strategy

### 2.1 Verified Datasets
| Dataset | Description | Source URL | Usage |
| :--- | :--- | :--- | :--- |
| **GBIF API** | Global Biodiversity Information Facility occurrence records. | (API endpoint) | Primary source for historical (1970‑2000) and recent (2005‑2020) bird records. |
| **eBird API** | Citizen‑science bird observations. | (API endpoint) | Supplementary source for recent records and effort data (bias layer). |
| **WorldClim v2** | Historical climate rasters (1970‑2000). | (FTP/HTTP endpoint) | Predictor variables for training. |
| **CMIP6** | Future climate scenario SSP2‑4.5 (2050). | (FTP/HTTP endpoint) | Predictors for projection. |
| **MaxEnt (csv)** | Small reference dataset for pipeline sanity check. | https://huggingface.co/datasets/maxentius42/dataset/resolve/main/dataset.csv | Validation of schema compatibility; not used for main analysis. |

### 2.2 Variable Fit & Mismatch Analysis
- **Outcome**: Presence/absence derived from GBIF/eBird (binary). ✔️  
- **Predictors**: bioclimatic variables from WorldClim (bio1‑bio19). ✔️  
- **Covariates**: Breeding‑season flag, spatial coordinates, bias raster (derived). ✔️  

No mismatches were identified; all required variables are available.

## 3. Methodology & Statistical Rigor

### 3.1 Data Preprocessing
1. **Filtering**: Retain records for target species; keep only dates falling within species‑specific breeding months.  
2. **Deduplication**: Remove exact coordinate duplicates.  
3. **Bias Correction**: `bias_correction.py` builds a target‑group effort raster from eBird/GBIF observation density; stored as `data/processed/bias_layer.tif`. Background points are sampled proportionally to this raster.  
4. **Spatial Thinning**: Apply a 10 km minimum distance filter (`spatial_thin`), satisfying FR‑002.  
5. **Climate Extraction**: Pull all 19 bioclim variables at each occurrence location using `rasterio`.  
6. **Provenance Logging**: **`logs/preprocess_counts.yaml` records `species`, `before_count`, `after_count`, and ISO‑8601 `timestamp` for every species processed.** This file serves as the Single Source of Truth for data reduction metrics, satisfying Constitution Principle VI.

All steps are reproducible with seeds defined in `code/config.py`.

### 3.2 Model Training (CPU‑Optimized)
- **Random Forest** – `sklearn.ensemble.RandomForestClassifier`.  
- **Bioclim** – custom envelope method based on percentile ranges of each predictor.  
- **Regularized Logistic Regression (Presence-Background)** – implemented via `sklearn.linear_model.LogisticRegression` with L2 regularization. **Note**: This is a Presence-Background method but is *not* the Maximum Entropy (MaxEnt) algorithm. It is used for its computational efficiency and interpretability. The plan and contracts explicitly reflect this distinction to avoid construct validity failures.

Training uses **Spatial Block Cross‑Validation** (K = 5) as mandated by FR‑007, ensuring spatial independence between folds.

### 3.3 Baseline Expectation (SC‑001)
A null model (`baseline.py`) predicts constant suitability equal to the prevalence of the training data. Its AUC/TSS are stored in `metrics/baseline_performance.csv` and serve as the baseline against which all SDM performances are compared.

### 3.4 Power Analysis (Methodology)
`power_analysis.py` calculates the minimum sample size required to detect a specific effect size (e.g., ΔAUC = 0.05) with [deferred] power, using a binomial proportion test approximation for AUC. Species with fewer than this calculated threshold are flagged as `UNDERPOWERED` and excluded from aggregate performance metrics. This replaces the arbitrary '100 record' threshold with a statistically derived one.

### 3.5 Projection & Evaluation
1. **Projection**: Apply each trained model to the 2050 SSP2‑4.5 raster (`project.py`).  
2. **Temporal Validation**: Evaluate against 2005‑2020 occurrence records (`evaluate.py`).  
3. **Bias-Corrected Background**: For the test set, pseudo-absence points are sampled using the **historical bias layer** (derived from 1970-2000 effort) to ensure the background distribution reflects historical sampling effort, preventing 'sampling bias mismatch' from confounding the degradation metric.  
4. **Metrics**: Compute AUC and True Skill Statistic (TSS).  
5. **Threshold Handling**: The optimal threshold is determined **solely on the training set** (via spatial block CV) and applied **unchanged** to the test set. This prevents data leakage and ensures the degradation metric reflects true predictive failure, not threshold adaptation to prevalence shift.  
6. **Statistical Tests**:  
   - Pairwise **Wilcoxon signed‑rank** tests between algorithms per species.  
   - **Benjamini‑Hochberg** correction for the family‑wise error rate (FR‑005).  
   - **Permutation tests** (10 000 permutations) for robust p‑values (FR‑010).  
7. **Niche Stability & Bias Null Model**: 
   - Compare performance on (historical → historical) vs. (historical → future) projections.
   - **Crucially**, compare the SDM degradation against a **Bias-Only Null Model** (`bias_null.py`) that predicts based solely on the change in sampling bias. If the SDM degradation is not significantly greater than the bias-only model's degradation, the result is attributed to bias, not niche non-stationarity.
8. **Framing**: All findings are **explicitly framed as associational**; the manuscript will include the disclaimer from `reports/associational_disclaimer.txt` (FR‑008).

### 3.6 Sensitivity Analysis (FR‑005, SC‑003)
`sensitivity.py` sweeps the absolute suitability‑probability difference Δ ∈ {0.01, 0.05, 0.10} for each model, recomputes TSS, and records headline rates (TPR, FPR, TSS) in `metrics/sensitivity_report.csv`. The report satisfies SC‑003 by providing a concise table of how performance varies across thresholds.

## 4. Compute Feasibility

- **Memory**: Raster chunks processed on‑the‑fly; peak RAM ≈ 5 GB.  
- **Runtime**: Benchmarked ≈ 4 h on GitHub Actions (2 CPU) for A diverse assemblage of species.  
- **No GPU**: All libraries are CPU‑only; `n_jobs` limited to 2.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Regularized Logistic Regression (PB)** | CPU-tractable Presence-Background method. Explicitly *not* MaxEnt. |
| **Target‑Group Bias Layer** | Corrects for spatial sampling bias, satisfying methodological rigor and preventing confounding of degradation signals. |
| **Baseline Null Model** | Provides a concrete reference for SC‑001; simple prevalence predictor ensures interpretability. |
| **Dynamic Power Threshold** | Replaces arbitrary '100' with a calculated minimum sample size for [deferred] power. |
| **Fixed Threshold from Training** | Prevents data leakage; ensures degradation metric reflects true predictive failure. |
| **Bias-Only Null Model** | Distinguishes model degradation from sampling bias shift. |
| **Benjamini‑Hochberg Correction** | Controls false discovery rate across multiple paired tests (FR‑005). |
| **Associational Disclaimer** | Directly satisfies FR‑008 and ensures transparent communication of observational limits. |
| **Sensitivity Report CSV** | Meets SC‑003 by delivering headline rates for each Δ sweep. |
| **Reference-Validator Agent** | Ensures Verified Accuracy via pre-commit hook and title-token-overlap check. |
| **Preprocessing Log (YAML)** | Satisfies Constitution Principle VI by providing a machine-readable, single-source-of-truth record of data reduction counts per species. |
