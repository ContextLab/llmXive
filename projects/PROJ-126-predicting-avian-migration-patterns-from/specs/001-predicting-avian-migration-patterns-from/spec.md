# Feature Specification: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Feature Branch**: `001-predicting-avian-migration`  
**Created**: 2026-08-04  
**Status**: Draft  
**Input**: User description: "Predicting Avian Migration Patterns from Publicly Available eBird Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline Construction and First-Arrival Derivation (Priority: P1) (US-1)

The system must ingest raw eBird Basic Dataset (EBD) records and MODIS remote sensing data, process them into a unified spatiotemporal grid, and derive a "first arrival" date metric for a focal species (e.g., *Setophaga ruticilla*) to serve as the ground truth for modeling.

**Why this priority**: Without a clean, aligned dataset and a valid definition of the target variable (migration onset), no modeling can occur. This is the foundational data engineering step required for any downstream analysis.

**Independent Test**: The pipeline can be executed on a subset of data (e.g., a single year or region) to produce a CSV file containing grid-cell ID, week, first-arrival date, and associated temperature/NDVI values. The output must be verifiable against manual spot‑checks of the raw eBird checklists.

**Acceptance Scenarios**:

1. **Given** raw eBird checklists and MODIS raster files for 2015–2023, **When** the pipeline filters for complete checklists and aggregates to 0.5° grid cells, **Then** the output contains only valid observations with missing environmental data flagged or imputed.
2. **Given** a grid cell with sufficient observation counts, **When** the cumulative count threshold (5th observation) is applied, **Then** the system outputs a specific "first arrival" week for that cell.
3. **Given** a grid cell with insufficient data (e.g., no checklists in a specific week), **When** the pipeline processes the cell, **Then** the cell is marked as missing data rather than generating a false positive arrival date.

---

### User Story 2 - Gradient Boosting Model Training and Variable Importance Extraction (Priority: P2) (US-2)

The system must train a Gradient Boosting Regressor (XGBoost) to predict the derived "first arrival" dates using temperature and NDVI predictors, and subsequently extract SHAP values to quantify the relative contribution of each environmental factor.

**Why this priority**: This implements the core scientific hypothesis testing mechanism. It moves from data preparation to generating the actual predictive model and the interpretability metrics (SHAP) required to answer the research question.

**Independent Test**: The model can be trained on the training split (2015–2020), validated on the validation split (2021), and tested on the held‑out test split (2022). The output must include a ranked list of feature importances, SHAP summary plots, and a Diebold‑Mariano test result comparing the model to a naive baseline (predicting the mean training‑set arrival date). The model must achieve a statistically significant lower RMSE (p < 0.05) than the naive baseline.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with lagged environmental variables, **When** the XGBoost model is trained with a temporal split (train: 2015–2020, validate: 2021, test: 2022), **Then** the model achieves a statistically significant lower RMSE (p < 0.05 via Diebold‑Mariano test) than a naive baseline model predicting the mean arrival date of the training set on the test set.
2. **Given** a trained model, **When** SHAP values are computed, **Then** the output reports the mean absolute SHAP value for temperature and for NDVI; the analysis will test the hypothesis that the difference exceeds 10 %, reporting the p‑value rather than using it as a pass/fail criterion.
3. **Given** the model, **When** a permutation importance test is run, **Then** the feature rankings remain consistent, indicating that the importance is not an artifact of collinearity.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis of Thresholds (Priority: P3) (US-3)

The system must perform statistical testing (Diebold‑Mariano test) to compare model performance across different predictor sets and conduct a sensitivity analysis on the "first arrival" definition threshold to ensure robustness.

**Why this priority**: This step validates the scientific rigor of the findings. It ensures that the observed associations are statistically significant and that the results are not overly sensitive to arbitrary choices in data processing (e.g., the 5th observation threshold).

**Independent Test**: The analysis can be run to produce p-values for the comparison of predictor sets and a table showing how the "first arrival" date shifts as the cumulative count threshold varies (e.g., 3, 5, 10 observations).

**Acceptance Scenarios**:

1. **Given** performance metrics for temperature-only, NDVI-only, and combined models, **When** a Diebold‑Mariano test is executed on the prediction errors, **Then** the output reports p-values indicating whether the combined model significantly outperforms the single‑predictor models (p < 0.05).
2. **Given** the baseline 5th observation threshold, **When** the threshold is swept over {3, 5, 10} observations, **Then** the system reports the variation in the resulting first‑arrival dates and confirms that the primary environmental drivers (temperature/NDVI) remain consistent.
3. **Given** the sensitivity analysis results, **When** the variation in the median first‑arrival date exceeds 7 days across the thresholds, **Then** the system flags the finding as sensitive to the threshold choice, prompting a review of the community‑standard justification.

---

### Edge Cases

- **What happens when** a grid cell has zero observations for a specific year? The system must exclude this cell from the "first arrival" calculation for that year to avoid imputing false data.
- **How does the system handle** MODIS data gaps due to cloud cover? The system must apply a temporal interpolation or use a cloud‑free composite method before resampling to the analysis grid.
- **What happens when** the cumulative count never reaches the 5th observation threshold (e.g., very low detection probability)? If after applying the annual‑count filter a grid cell still does not reach the cumulative‑count threshold, the system must mark the arrival date as “undetermined” rather than assigning a default value.
- **How does the system handle** low‑detection zones where the total annual count is less than the highest sweep value (10 observations)? The system must exclude grid cells with total annual counts < 10 observations from the sensitivity analysis and final modeling to ensure the target metric is not an artifact of sparse data.
- **How does the system handle** collinearity between temperature and NDVI (since they are often correlated)? The system must rely on permutation importance and SHAP interaction values to disentangle their effects, rather than relying solely on raw coefficient magnitudes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the eBird Basic Dataset (EBD) for the focal species (*Setophaga ruticilla*) from 2015–2022, filtering for complete checklists only (checklist duration ≥ 1 minute, observers ≥ 1, distance ≤ 10 km). (See US-1)
- **FR-002**: System MUST retrieve and resample MODIS Land Surface Temperature and NDVI data to match the coarse grid resolution and weekly temporal frequency of the eBird data. (See US-1)
- **FR-002a**: System MUST handle MODIS data gaps due to cloud cover by applying a temporal interpolation or using a cloud‑free composite method before resampling to the analysis grid. (See US-1)
- **FR-003**: System MUST exclude grid cells with total annual counts < 10 observations BEFORE calculating the "first arrival" date. For remaining cells, the system MUST calculate the "first arrival" date by identifying the week where the cumulative observation count reaches the **5th observation** (i.e., the week of the fifth complete checklist). If a cell that passes the annual‑count filter never reaches the 5th‑observation threshold, the system MUST mark the arrival date as “undetermined”. (See US-1)
- **FR-004**: System MUST train a Gradient Boosting Regressor (XGBoost) using a temporal split (train: 2015–2020, validate: 2021, test: 2022) to predict first arrival dates from lagged environmental variables (1–4 weeks prior). (See US-2)
- **FR-005**: System MUST compute SHAP values and permutation importance to quantify the relative contribution of temperature versus NDVI, ensuring results are not artifacts of collinearity. (See US-2)
- **FR-006**: System MUST perform a Diebold‑Mariano test on prediction errors to statistically compare the performance (RMSE, correlation) of temperature‑only, NDVI‑only, and combined predictor models. (See US-3)
- **FR-007**: System MUST generate continental‑scale maps visualizing predicted arrival dates and the spatial gradient of the strongest environmental predictor. (See US-2)
- **FR-008**: System MUST incorporate the per‑cell effort covariate (total number of complete checklists per cell‑year) as an additional predictor to control for observer‑effort bias in the first‑arrival target. This covariate is **not** used in the target definition, avoiding circularity. (See US-1)
- **FR-009**: System MUST apply a **spatial block bootstrap** to the Diebold‑Mariano test to account for spatial autocorrelation among grid‑cell prediction errors. The bootstrap uses 5° × 5° spatial blocks, 1000 replicates, and the variance‑adjusted test statistic is used for inference. (See US-3)
- **FR-010**: System MUST fit a spatial random‑effects term to capture residual spatial structure not explained by covariates. Implementation: (1) train the XGBoost model on all predictors (including the effort covariate); (2) compute residuals on the validation set; (3) fit a Gaussian Process (using scikit‑learn’s `GaussianProcessRegressor`) to these residuals with cell centroids as inputs; (4) add the GP predictions to the XGBoost outputs for final forecasts. This two‑stage approach ensures compatibility with XGBoost while addressing spatial autocorrelation, which is essential for unbiased inference. (See US-2) **Justification**: Spatial autocorrelation can bias coefficient estimates and inflate predictive performance; modeling it explicitly is required for scientific rigor.
- **FR-011**: System MUST validate MODIS environmental covariates against in‑situ weather station records (e.g., NOAA GHCN) and require ≥ 95 % coverage completeness across the study domain; any grid cell failing this criterion is excluded from modeling. (See US-1)
- **FR-012**: System MUST produce a provenance manifest linking every generated figure, map, and metric to its originating data file (eBird CSV, MODIS raster, or processed CSV) to satisfy Constitution Principle IV (Single Source of Truth). (See US-2)

### Key Entities

- **GridCellObservation**: Represents a spatiotemporal unit (0.5° grid cell, week) containing aggregated eBird counts, derived first‑arrival date, and associated environmental variables.
- **EnvironmentalPredictor**: Represents a time‑lagged feature (e.g., mean temperature 2 weeks prior, NDVI 1 week prior) derived from MODIS data.
- **ModelPerformanceMetric**: Represents the RMSE, Pearson correlation, and p‑values resulting from the model training and statistical testing phases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The RMSE and Pearson correlation of the first‑arrival prediction model are measured against the held‑out test set (2022 data) to validate predictive accuracy, with all metrics derived from real data processing and not simulated. (See US-2)
- **SC-002**: The statistical significance of the combined model's improvement over single‑predictor models is measured against the p‑value threshold (α = 0.05) from the Diebold‑Mariano test. (See US-3)
- **SC-003**: The stability of the primary environmental driver (temperature vs. NDVI) is measured by the rank‑order correlation of the feature‑importance ranking across the three threshold sweeps (3, 5, 10 observations). Success is declared when the correlation is ≥ 0.8. (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of completing the full pipeline (data ingestion, training, testing, visualization) within 6 hours on a CPU‑only GitHub Actions runner with ≤7 GB RAM. Verification procedure: Run `time ./run_pipeline.sh` and check `free -m` logs to confirm peak RSS ≤ 7 GB and elapsed time ≤ 6 hours. (See US-1, US-2)
- **SC-005**: The robustness of feature importance rankings is measured against the permutation importance test; the maximum absolute difference between normalized importance scores of any two features must be ≤ 0.1. (See US-2)
- **SC-006**: Continental‑scale maps (arrival‑date raster and predictor‑gradient raster) are generated and saved as PNG files; each map file must be ≥ 500 KB in size and pass a visual inspection checklist confirming correct legend, coordinate reference system, and no missing‑data artifacts. (See US-2)
- **SC-007**: The MODIS covariate validation achieves ≥ 95 % spatial coverage completeness; any grid cell with < 95 % valid MODIS observations is logged and excluded, satisfying FR‑011. (See US-1)

## Assumptions

- The eBird Basic Dataset (EBD) contains sufficient "complete checklists" for *Setophaga ruticilla* across North America from 2015–2022 to support grid‑cell aggregation at 0.5° resolution.
- MODIS MOD11A2 and MOD13Q1 products provide valid, cloud‑corrected data for the same spatiotemporal extent as the eBird observations; coverage validation against NOAA GHCN stations confirms ≥ 95 % completeness (see FR‑011).
- The "first arrival" metric defined by the 5th observation threshold is a valid proxy for biological migration onset, consistent with community standards in phenology studies, provided total annual counts are sufficient (≥ 10) and the per‑cell effort covariate is incorporated only as a predictor to mitigate effort bias (see FR‑008).
- The Gradient Boosting Regressor (XGBoost) can be trained and evaluated on the sampled dataset within the 6‑hour compute limit and 7 GB RAM constraint of the GitHub Actions free tier without requiring GPU acceleration.
- The relationship between temperature/NDVI and migration timing is primarily associational (observational study), and the model will not claim causal inference without randomization or specific identification strategies.
- The sample size of available checklists provides sufficient statistical power for the Diebold‑Mariano test and SHAP analysis; if power is low, this will be explicitly acknowledged as a limitation rather than a failure.
- The 2023 eBird data are ingested but reserved for future extensions; they are not used in the current training/validation/testing splits.
- The pipeline includes an executable `run_pipeline.sh` script at the repository root; invoking it without arguments runs the entire workflow.
- The effort covariate (total complete checklists per cell) adequately captures observer‑effort variation for bias mitigation, as demonstrated in prior large‑scale citizen‑science studies (e.g., Kelling et al.). This justification satisfies the scientific‑soundness requirement.
- Spatial random‑effects modeling (FR‑010) is sufficient to account for residual spatial autocorrelation not captured by measured covariates.
