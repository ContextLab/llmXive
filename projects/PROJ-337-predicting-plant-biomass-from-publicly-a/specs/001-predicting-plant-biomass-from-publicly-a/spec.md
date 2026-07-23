# Feature Specification: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

**Feature Branch**: `001-predict-plant-biomass`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Biomass from Publicly Available Hyperspectral Imagery"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download the HyBiomass benchmark dataset and NEON hyperspectral data, apply atmospheric correction (e.g., FLAASH/LEDAPS), and extract ground-truth biomass values to create a clean, analysis-ready dataset.

**Why this priority**: Without a reproducible, clean dataset containing both spectral inputs and ground-truth labels, no modeling or analysis can occur. This is the foundational step.

**Independent Test**: The pipeline can be fully tested by running the download and preprocessing scripts on a sample subset (e.g., 5 sites) and verifying that the output CSV contains valid spectral bands, corrected reflectance values, and non-null biomass labels.

**Acceptance Scenarios**:

1. **Given** the HyBiomass and NEON data sources are accessible, **When** the download script executes, **Then** the raw hyperspectral cubes and metadata files are stored locally with checksums verified.
2. **Given** raw hyperspectral cubes are available, **When** the atmospheric correction module runs, **Then** the output reflectance values fall within the physically valid range [0, 1] and the processing log confirms successful completion for all scenes.
3. **Given** preprocessed spectral data exists, **When** the ground-truth extraction script runs, **Then** a final dataset table is generated where every row has a matching biomass value and no more than 5% of rows are dropped due to missing metadata.

---

### User Story 2 - Baseline Model Training and Evaluation (Priority: P2)

The researcher MUST be able to train a Random Forest and a TabPFN model on the prepared dataset using 5-fold cross-validation, and evaluate their performance against a null baseline (predicting the mean) using RMSE, MAE, and R².

**Why this priority**: This establishes the performance ceiling and determines if the signal in the public data is sufficient for prediction. It directly addresses the core research question regarding feasibility.

**Independent Test**: The modeling step can be tested independently by running the training script on a fixed random seed and verifying that the output metrics (RMSE, MAE, R²) are generated and that the TabPFN model completes within the 6-hour CPU time limit.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset is split into train/validation/test sets, **When** the Random Forest model trains, **Then** the model converges without memory errors and produces a cross-validated R² score.
2. **Given** the same dataset, **When** the TabPFN model trains, **Then** the inference completes on CPU without CUDA errors and produces a cross-validated R² score.
3. **Given** the trained models, **When** the evaluation script runs, **Then** the RMSE and MAE are calculated against the test set and compared against the null baseline (mean predictor), with the results logged.

---

### User Story 3 - Ablation Study and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to quantify the impact of atmospheric correction and structural complexity by running an ablation study (with/without correction, with/without structural features) and performing a sensitivity analysis on decision thresholds or feature inclusion criteria.

**Why this priority**: This addresses the "how" in the research question, isolating the specific contributions of atmospheric effects and structural complexity to prediction accuracy.

**Independent Test**: The ablation study can be tested by re-running the training pipeline with specific feature subsets disabled and verifying that the performance metrics change as expected (e.g., performance drops when structural features are removed).

**Acceptance Scenarios**:

1. **Given** the full model configuration, **When** the ablation study runs with "no atmospheric correction", **Then** the resulting RMSE is recorded and compared to the "with correction" baseline to quantify the penalty.
2. **Given** the structural feature set, **When** the model is trained without structural proxies (e.g., canopy height), **Then** the change in R² is logged to quantify the contribution of structural complexity.
3. **Given** a specific decision threshold (e.g., feature importance cutoff), **When** the sensitivity analysis sweeps the threshold over a range (e.g., 0.01, 0.05, 0.1), **Then** the false-positive and false-negative rates are reported for each step.

---

### Edge Cases

- What happens when the atmospheric correction fails for a specific scene due to cloud cover? (System should flag and exclude the scene, logging the count).
- How does the system handle sites where ground-truth biomass data is missing or inconsistent with spectral coverage? (System should drop the row and report the exclusion rate).
- How does the system handle memory spikes when loading full hyperspectral cubes? (System must implement chunked loading or down-sampling to stay within 7GB RAM).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and cache the HyBiomass and NEON datasets, verifying integrity via checksums. (See US-1)
- **FR-002**: The system MUST apply atmospheric correction to raw hyperspectral cubes, ensuring output reflectance is within [0, 1]. (See US-1)
- **FR-003**: The system MUST extract ground-truth biomass values from metadata, dropping rows with missing values and logging the exclusion rate. (See US-1)
- **FR-004**: The system MUST train Random Forest and TabPFN models using 5-fold cross-validation, ensuring execution completes within 6 hours on a CPU-only environment. (See US-2)
- **FR-005**: The system MUST evaluate model performance using RMSE, MAE, and R², comparing results against a null baseline (mean predictor) to determine statistical significance (p < 0.05). (See US-2)
- **FR-006**: The system MUST perform an ablation study by toggling atmospheric correction and structural features, recording the delta in performance metrics for each configuration. (See US-3)
- **FR-007**: The system MUST conduct a sensitivity analysis sweeping key thresholds (e.g., feature importance cutoffs) over a defined range (e.g., 0.01, 0.05, 0.1) and report the variation in false-positive/negative rates. (See US-3)
- **FR-008**: The system MUST implement multiple-comparison correction (e.g., Bonferroni or FDR) when evaluating the significance of ablation study results across multiple hypotheses. (See US-3)

### Key Entities

- **HyperspectralCube**: Represents a spatially indexed set of spectral reflectance values across hundreds of bands.
- **SiteMetadata**: Contains location, environmental context, and ground-truth biomass values (LIDAR/field derived).
- **ModelResult**: Stores performance metrics (RMSE, MAE, R²) and hyperparameters for a specific model configuration.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction accuracy (RMSE) is measured against the null baseline (predicting the mean biomass) to determine if the public data provides a statistically significant signal. (See US-2)
- **SC-002**: The impact of atmospheric correction is measured by comparing the R² of models trained on corrected vs. uncorrected data. (See US-3)
- **SC-003**: The contribution of structural complexity is measured by comparing the R² of models with and without structural proxies (e.g., canopy height). (See US-3)
- **SC-004**: The robustness of the model to threshold selection is measured by the variance in false-positive rates across the sensitivity sweep (0.01, 0.05, 0.1). (See US-3)
- **SC-005**: The computational feasibility is measured by ensuring the total runtime for the full pipeline (download, preprocess, train, evaluate) remains [deferred] on a standard CPU runner. (See US-2)

## Assumptions

- The HyBiomass and NEON datasets are publicly accessible via the provided URLs and do not require proprietary authentication.
- The "ground-truth" biomass values provided in the dataset metadata are derived from LIDAR or field measurements and are considered the reference standard for evaluation.
- Atmospheric correction algorithms (FLAASH/LEDAPS) are available in a Python-compatible library (e.g., `pysptools` or `atmcorr`) that can run on CPU without CUDA.
- The dataset size, even after full hyperspectral cube loading, can be managed within 7GB RAM via chunked processing or strategic subsampling if necessary.
- The TabPFN implementation provided in the literature precedent can be executed in a CPU-only environment without requiring 8-bit quantization or GPU acceleration.
- The research design is observational; therefore, all findings regarding "impact" or "effect" are framed as associational correlations, not causal claims.
- The dataset contains all necessary variables (spectral bands, biomass labels, and structural proxies) as described in the HyBiomass documentation; if a specific structural proxy (e.g., canopy height) is missing for a subset, the analysis will proceed with available data and note the limitation.
- The multiple-comparison correction method (e.g., Bonferroni) will be applied to the set of hypothesis tests conducted in the ablation study to control family-wise error rate.
- The sensitivity analysis will sweep the decision threshold over the absolute difference set {0.01, 0.05, 0.1} as a defensible community-standard default for this domain.
