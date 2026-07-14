# Research: 001-predict-root-architecture

## Executive Summary

This research phase defines the data strategy, statistical methodology, and computational constraints for predicting plant root architecture from soil nutrients. The analysis focuses on quantifying associational relationships between Phosphorus (P) and Nitrogen (N) concentrations and root traits (length, branching, surface area) using Linear Mixed-Effects Models.

## Dataset Strategy

### Verified Datasets
Per the "Verified datasets" block, the following sources are available. **Note:** RootReader and ISRIC have **NO verified source found**.
*Resolution:* The pipeline will fetch **PlantPheno** (Root Phenotype) from the verified HuggingFace URL. For **Soil Nutrients (ISRIC)**, the pipeline requires a user-provided CSV file (`data/raw/isric_data.csv`) matching the `raw_soil_nutrient` schema. If this file is missing, the pipeline will **halt with a clear error** rather than generating synthetic data, ensuring that any scientific results are based on real data (Constitution Principle I). A small, static mock dataset is used *only* for structural CI testing (schema validation) with a disclaimer that no scientific inference is drawn.

**Available Verified Sources:**
1. **PlantPheno (Root Phenotype)**:
 * Train: `
 * Test: `
 * *Usage:* Primary source for root metrics (length, branching) and species.
 * *Constraint Check:* Must verify if these files contain `geographic_location`. If not, the merge will fail, and the pipeline will halt.

2. **Soil Nutrients (ISRIC)**:
 * *Status:* No verified URL.
 * *Requirement:* User must provide `data/raw/isric_data.csv` with columns: `latitude`, `longitude`, `phosphorus_concentration`, `nitrogen_concentration`.
 * *Reproducibility:* The pipeline is reproducible only if the user provides the same file on every run.

### Data Integration Strategy
1. **Fetch PlantPheno**: Download from verified HuggingFace URL.
2. **Load Soil Data**: Attempt to load `data/raw/isric_data.csv`. If missing, raise `DataNotFoundError`.
3. **Merge Logic**: Merge on `geographic_location` (lat/lon) using nearest-neighbor interpolation (10km radius) as per FR-002.
 * **Spatial Confounding Mitigation**: Since 10km interpolation introduces spatial noise, `latitude` and `longitude` will be included as **fixed effects** in the LMM to control for spatial trends.
 * **Limitation**: The nutrient predictor is a spatially smoothed proxy. The resulting coefficient is an attenuated estimate (lower bound) of the true local effect. This is explicitly acknowledged in the report.

### Dataset Variable Fit Analysis
* **RootPhenotypeRecord**: Expected fields: `species`, `root_length`, `branching_density`, `surface_area`, `geographic_location`, `data_source_type`.
* **SoilNutrientRecord**: Expected fields: `phosphorus_concentration`, `nitrogen_concentration`, `geographic_location`, `depth`.
* **Gap Risk**: If PlantPheno lacks `geographic_location`, the merge fails.
 * *Mitigation:* The `data_ingestion.py` script will perform a schema check. If columns are missing, it will log an exclusion (SC-005) and halt if the core requirement (P/N prediction) cannot be met.

## Statistical Methodology

### Model Selection
* **Primary Model**: Linear Mixed-Effects Model (LMM) using `statsmodels`.
 * **Fixed Effects**: `log(phosphorus)`, `log(nitrogen)`, `latitude`, `longitude`.
 * **Random Effects**: `(1 | species)`.
 * **Estimation**: REML (Restricted Maximum Likelihood).
 * **P-values**: Satterthwaite approximation.
* **Baseline Model**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
 * **Parameters**: `max_depth=5`, `random_state=42`.
 * **Purpose**: Capture non-linear relationships (FR-005).

### Validation Strategy (Constitution Principle VI)
* **Splitting**: 5-fold Cross-Validation **by Species**.
 * Folds are created by grouping unique species names.
 * No row-level shuffling.
 * Ensures the model generalizes to *new* species, not just new observations of known species.
 * **Random Effect Handling**: The random intercept `(1 | species)` captures baselines for *known* species. For *new* species (test set), the model relies on fixed effects (nutrients) for prediction.
* **Metrics**:
 * **Predictive**: Adjusted R², RMSE, Mean Out-of-Sample R².
 * **Coefficient Stability**: Standard deviation of nutrient coefficients across the 5 folds. High stability is required to validate the associational claim (Scientific Soundness concern).

### Imputation Strategy (Data Leakage Prevention)
* **Method**: KNN Imputation (k=5, Euclidean distance).
* **Procedure**: **Fit-then-Apply**.
 1. Split data into Train/Validation/Test folds by species.
 2. Fit the KNN imputer **only on the Training fold**.
 3. Apply the fitted imputer to the Training and Validation/Test folds.
 4. **Predictor-Only**: Imputation uses only predictor variables (nutrients, lat/lon). Outcome variables (root traits) are **excluded** from the distance calculation to prevent circularity.
 5. **No Mean Fallback for Test**: If a test sample has no neighbors in the training set, it is excluded from that fold's evaluation to avoid distribution shift.

### Statistical Rigor & Corrections
* **Overall Model Significance (FR-008)**: Perform a **Likelihood Ratio Test (LRT)** comparing the full model (with nutrients) against a null model (intercept only + random effects). Report the LRT p-value.
* **Multiple Comparisons**: Bonferroni correction applied to p-values when testing multiple traits (length, density, area) or multiple nutrients (FR-010).
* **Causal Framing**: All findings reported as **associational** (FR-009). No causal claims.
* **Collinearity**: P and N often correlate. Variance Inflation Factor (VIF) will be calculated. If VIF > 5, coefficients will be interpreted with caution.
* **Power Analysis**: Species with n < 20 are excluded. Species with 20 <= n < 30 are included but flagged as "Low-Power Random Effect" in the report.

### Biological Plausibility Check (FR-011, SC-006)
* **Method**: Compare the calculated nutrient coefficients (and their 95% CI) against literature-reported physiological ranges.
* **Source**: Ranges will be sourced from the PlantPheno metadata or cited literature in `research.md`.
* **Success**: The 95% CI of the coefficient must overlap with the literature range.
* **Reporting**: The final report will explicitly state whether the result is biologically plausible.

## Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, No GPU).
* **Strategy**:
 * **Data Sampling**: If the merged dataset exceeds ~500k rows, a stratified sample (by species) will be taken to ensure memory safety.
 * **Libraries**: `statsmodels` and `scikit-learn` are CPU-optimized. No deep learning or GPU quantization.
 * **Runtime**: Target < 2 hours for full pipeline.
 * **Storage**: Output figures compressed to PNG; total size < 100 MB (FR-007, SC-004).

## Decision Log & Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use PlantPheno (HF) for roots** | Only verified dataset for root phenotypes available. |
| **Manual ISRIC Data** | No verified URL for ISRIC. Pipeline halts if missing to ensure scientific validity. |
| **Species-Level Split** | Mandated by Constitution Principle VI to prevent data leakage. |
| **LMM over OLS** | Required to account for species-level random effects (hierarchical data). |
| **Fit-then-Apply Imputation** | Prevents data leakage and distribution shift (Methodology concern). |
| **LRT for Significance** | Statistically correct method for LMM global significance (FR-008). |
| **Coefficient Stability Metric** | Validates the associational claim, not just predictive power (Scientific Soundness concern). |
| **Spatial Fixed Effects** | Mitigates confounding from 10km interpolation (Scientific Soundness concern). |