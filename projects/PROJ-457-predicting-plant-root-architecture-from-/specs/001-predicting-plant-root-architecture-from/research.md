# Research: 001-predict-root-architecture

## Executive Summary

This research plan investigates the associational relationship between soil Phosphorus (P) and Nitrogen (N) concentrations and plant root architectural traits (length, branching density, surface area). The study leverages public datasets to construct a merged dataset, applies rigorous preprocessing (log-transform, exclusion of missing data), and fits Linear Mixed-Effects Models (LMM) with species as a random effect. A Random Forest baseline and cross-species validation are employed to assess model robustness and generalization. All findings are framed as associational, with sensitivity analyses conducted against literature ranges.

**CRITICAL DATA LIMITATION**: The spec (FR-002) mandates merging with ISRIC-World Soil Information. However, no verified ISRIC source exists in the project's `# Verified datasets` block. The primary source (PlantPheno) may lack explicit P/N columns. Consequently, the pipeline **cannot** fulfill the core spec requirement to link root phenotypes to ISRIC data. The implementation will proceed ONLY with the verified PlantPheno dataset. If PlantPheno lacks P/N columns, the "Nutrient Prediction" hypothesis will be flagged as **Unverifiable** in the final report.

## Dataset Strategy

### Verified Datasets
The following datasets are the only sources used, as verified in the project context:

| Dataset Name | Source URL | Usage in Plan |
|:--- |:--- |:--- |
| **PlantPheno** | `<br>` | Primary source for root phenotype data (root length, branching, species). **Check for P/N columns.** |

**Note on Unverified Sources**: The spec mentions `RootReader` and `ISRIC-World Soil Information` as primary sources. However, the `# Verified datasets` block explicitly states **"NO verified source found"** for these.
* **Action Plan**: The ingestion pipeline (`code/ingestion.py`) will attempt to load the PlantPheno data.
 1. Check if the PlantPheno data contains explicit P/N columns.
 2. If **YES**: Proceed with the analysis as planned.
 3. If **NO**: **STOP** the nutrient merge logic. The project will analyze root metrics only. The "Nutrient Prediction" hypothesis is flagged as **Unverifiable** due to data unavailability. No fallback to unverified datasets (e.g., `blanchon/merged_dataset`) is permitted.

### Data Integration & Merging
* **Strategy**: If `PlantPheno` lacks nutrient data, the project scope is adjusted. **No fallback to unverified datasets**.
* **Geospatial Matching**: If geospatial matching is required (e.g., merging PlantPheno with a hypothetical ISRIC source), the plan will use `geopandas` and `nearest neighbor` interpolation **only if** `latitude` and `longitude` (floats) are present. If coordinates are missing, the observation is excluded. The '10km interpolation' is a theoretical requirement for FR-002 that cannot be executed due to data constraints.
* **Filtering**:
 * Exclude species with $n < 20$ (FR-001, US-1).
 * Exclude experimental/controlled data if `data_source_type` is available (FR-012).
 * **Exclude rows with missing P/N values** (no imputation) to avoid bias (FR-003 deviation).

## Statistical Methodology

### Model Selection
1. **Linear Mixed-Effects Model (LMM)**:
 * **Formula**: `root_metric ~ phosphorus + nitrogen + (1 | species)`
 * **Estimation**: REML (Restricted Maximum Likelihood).
 * **Inference**: Satterthwaite approximation for degrees of freedom and p-values (FR-004).
 * **Rationale**: Accounts for non-independence of observations within species (random intercept) while estimating fixed effects of nutrients.
 * **Mitigation for Confounding**: To address species-nutrient confounding (scientific soundness concern), a secondary **Within-Species** analysis or **Interaction Model** (`root_metric ~ phosphorus * species`) will be fitted. This tests if the nutrient effect varies by species, addressing the non-identifiability of the fixed effect in the primary LMM.
2. **Random Forest Regressor**:
 * **Parameters**: `max_depth=5`, `n_estimators=100`.
 * **Rationale**: Baseline for non-linear relationship detection (FR-005). **Note**: R² comparison is for model complexity assessment, not validity.

### Validation Strategy
* **Cross-Species Stratified Split**: Folds are created by `species` ID, not by row, to prevent data leakage (FR-006, Constitution Principle VI).
* **Metrics**: Adjusted $R^2$, RMSE, p-values for coefficients.
* **Multiple Comparison Correction**: Bonferroni or False Discovery Rate (FDR) applied to p-values when testing multiple nutrients/traits (FR-010).

### Power Analysis
* **Effective Sample Size**: For LMM, the effective sample size is determined by the number of species (groups) and the number of observations per group.
 * Formula: $N_{eff} \approx \frac{N_{species} \times N_{obs}}{1 + (N_{obs} - 1) \times ICC}$, where ICC is the Intraclass Correlation Coefficient.
* **Minimum Detectable Effect (MDE)**: The MDE is defined based on the expected number of species and observations. If the number of species is small (e.g., < 10), the power to detect small-to-moderate nutrient effects may be insufficient, leading to Type II errors.
* **Limitation**: If the number of species is small, the power to detect small-to-moderate nutrient effects may be insufficient. This limitation will be explicitly noted in the final report.

### Confounding & Identification
* **Species-Nutrient Confounding**: Acknowledged that specific species may be restricted to specific soil types. The LMM treats species as a random effect, which may absorb the nutrient effect.
* **Mitigation**: **Within-Species** analysis or interaction modeling is used to test if the nutrient effect is consistent across species. If not possible, interpret results as associational within the context of species-specific constraints.

### Spatial Scale & MAUP
* **Scale Mismatch**: Acknowledged that root data is often from specific root zones while ISRIC provides global soil grid averages.
* **Mitigation**: If coordinates are present, use spatial autocorrelation models or aggregate data to a consistent scale. If coordinates are missing (as in the primary source), the observation is excluded. The MAUP risk is acknowledged and the limitation is noted.

### Sensitivity & Plausibility (FR-011)
* **Literature Ranges**: Coefficients will be compared against known physiological ranges for P and N effects on root growth.
* **Sensitivity Analysis**: Coefficients will be re-calculated with $\pm 10\%$ variation in input nutrient values to assess stability.
* **Literature Comparison**: The final report will include a section comparing the calculated coefficients to published physiological ranges. The `literature_overlap` boolean will be calculated: True if the 95% CI of the coefficient overlaps with the literature range.
* **SC-006 Measurement**: `literature_overlap` is calculated as True if the 95% CI of the coefficient overlaps with the literature range.

## Compute Feasibility & Data Handling

### CPU-First Approach
* **Environment**: GitHub Actions (2 CPU, 7 GB RAM).
* **Strategy**:
 * Use `statsmodels` (CPU-optimized) for LMM.
 * Use `scikit-learn` (CPU) for Random Forest.
 * **Streaming**: If the dataset is large, use `datasets.load_dataset(..., streaming=True)` to process data in chunks.
 * **Sampling**: If the full dataset exceeds a substantial processing duration, a fixed-seed random sample will be used., with the limitation explicitly noted in the report.

### GPU Escape Hatch
* **Decision**: Not required. The proposed methods (LMM, RF) are computationally tractable on CPU. No transformer or diffusion models are used.

## Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **Missing Nutrient Data** | Observations lacking P/N are **excluded** (not imputed). The pipeline logs the exclusion count and proceeds. No synthetic data is generated. **Spec Deviation** from FR-003. |
| **Experimental Data Contamination** | Strict filtering on `data_source_type` (if present) or exclusion of rows with known experimental markers. |
| **Data Leakage** | Enforced by `GroupKFold` split on `species` ID. |
| **Collinearity** | P and N are often correlated. VIF (Variance Inflation Factor) will be calculated; if high, results will be reported as "joint effect" or individual effects will be interpreted with caution. |
| **Species-Nutrient Confounding** | Addressed via **Within-Species** analysis or interaction terms. |
| **Spatial Scale Mismatch** | Addressed by excluding observations without coordinates. Limitation noted. |
| **Unverifiable Hypothesis** | If PlantPheno lacks P/N columns, the "Nutrient Prediction" hypothesis is flagged as **Unverifiable** in the final report. |

## Decision Rationale

* **Method**: LMM chosen over OLS to handle species-level clustering. RF chosen as a non-linear baseline.
* **Data**: PlantPheno selected as the only verified source. ISRIC is excluded from the active pipeline due to lack of verified URL, preventing fabrication. Observations lacking P/N are excluded.
* **Validation**: Cross-species split is mandatory to satisfy Constitution Principle VI and ensure generalization.
* **Spec Deviation**: The plan explicitly acknowledges deviations from FR-002 (ISRIC merge) and FR-003 (KNN imputation) due to data availability and scientific validity. These deviations will be flagged in the final report.