# Feature Specification: Understanding Oceanic Phytoplankton Communities through Remote Sensing and Oceanographic Data

**Feature Branch**: `001-phytoplankton-vlm-analysis`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "How do oceanographic conditions (temperature, salinity, nutrient availability) drive the spatial-temporal distribution and abundance of phytoplankton communities across different ocean basins?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest, align, and preprocess multi-modal satellite ocean color data (MODIS), oceanographic reanalysis data (temperature, salinity, nutrients), and in-situ measurements (SeaBASS/BGC-Argo) to create a unified, CPU-tractable dataset ready for analysis.

**Why this priority**: Without a clean, aligned dataset with independent ground truth, no modeling or analysis can occur. This is the foundational step that ensures data integrity, statistical validity, and feasibility within the 6-hour CPU and 7GB RAM constraints.

**Independent Test**: Can be fully tested by running the data pipeline script on a sample subset of ocean basins and verifying that the output is a single, aligned CSV/netCDF file with no missing values due to temporal or spatial misalignment, and that the memory usage does not exceed 7GB RAM during execution.

**Acceptance Scenarios**:

1. **Given** raw MODIS, reanalysis, and in-situ data files for the North Atlantic, **When** the preprocessing script executes, **Then** the output file contains aligned monthly composites at 4km resolution with no spatial gaps exceeding 5% of the total grid cells.
2. **Given** a dataset with missing temporal entries for specific months, **When** the script processes the data, **Then** it applies linear interpolation for gaps ≤ 2 months, quantifies the interpolation error, and flags larger gaps for exclusion rather than imputation.
3. **Given** data spanning multiple ocean basins, **When** the script runs, **Then** it correctly stratifies the data by basin, retains the basin identifier in every record, and applies a unified masking strategy for all missing data points before model evaluation.

---

### User Story 2 - Baseline and VLM Model Training (Priority: P2)

The system must train and evaluate both a baseline Random Forest regression model and a lightweight CLIP-based VLM (<500M parameters) using the preprocessed dataset to predict phytoplankton abundance from environmental drivers.

**Why this priority**: This is the core scientific experiment. It directly addresses the research question by comparing traditional statistical methods against the novel VLM approach to determine if VLMs offer superior predictive power.

**Independent Test**: Can be fully tested by executing the training script on the training set, evaluating on the validation set, and reporting RMSE and R² metrics for both models without requiring human intervention or external API calls.

**Acceptance Scenarios**:

1. **Given** the training dataset, **When** the Random Forest model trains, **Then** it completes within 2 hours and produces an R² score and RMSE on the validation set.
2. **Given** the training dataset, **When** the lightweight CLIP-based VLM (<500M parameters) fine-tunes, **Then** it completes within 4 hours on CPU, uses ≤ 7GB RAM, and either converges (loss decreases over 3 epochs) or triggers an early stopping mechanism that logs the failure and defaults to the baseline model performance for that run.
3. **Given** both trained models, **When** evaluated on the held-out test set, **Then** the system outputs a comparison table containing RMSE, R², and MAE for both the baseline and VLM models.

---

### User Story 3 - Feature Importance and Driver Quantification (Priority: P3)

The system must quantify the contribution of specific environmental drivers (temperature, salinity, nutrients) to phytoplankton distribution using permutation importance and generate spatial visualization maps of these contributions.

**Why this priority**: This delivers the specific scientific insight required by the research question: identifying *which* drivers are most influential. It transforms model predictions into actionable ecological understanding.

**Independent Test**: Can be fully tested by running the feature importance analysis on the trained VLM and verifying that the output includes a ranked list of drivers and a spatial map file (e.g., GeoTIFF or PNG) showing regional variation.

**Acceptance Scenarios**:

1. **Given** the trained VLM model, **When** permutation importance is calculated, **Then** the system outputs a ranked list of drivers where the sum of all importance scores equals 1.0 (within a tolerance of 0.01).
2. **Given** the feature importance results, **When** the visualization script runs, **Then** it generates a map showing the spatial distribution of the most important driver (e.g., temperature) with a color scale legend.
3. **Given** the test set predictions and the independent in-situ dataset, **When** the correlation analysis runs, **Then** it reports the correlation coefficient (r) between predicted and in-situ measurements for each ocean basin separately.

### Edge Cases

- **What happens when** in-situ data is missing for a specific month in a specific basin? The system must exclude that grid cell from the training set for that month rather than attempting to impute, to avoid introducing bias.
- **How does the system handle** extreme outliers in ocean color data (e.g., cloud contamination)? The system must apply a strict quality flag filter (e.g., MODIS l2 flags) to exclude pixels with "cloud" or "high aerosol" flags before preprocessing.
- **What happens when** the VLM training loss does not decrease after 3 epochs? The system must trigger an early stopping mechanism, log a warning, and default to the baseline model performance for that run to ensure a valid comparison is always produced.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest MODIS Aqua/Terra ocean color data, NOAA/Copernicus reanalysis data, and in-situ data (SeaBASS/BGC-Argo), aligning them to a common spatial grid and monthly temporal resolution using a unified masking strategy for missing data (See US-1).
- **FR-002**: System MUST implement a Random Forest baseline model with ≤ 500 trees using scikit-learn on CPU to establish a performance benchmark (See US-2).
- **FR-003**: System MUST fine-tune a lightweight CLIP-based VLM (<500M parameters) using concatenated image patches and text prompts derived from oceanographic metadata on CPU only (See US-2).
- **FR-004**: System MUST perform permutation importance testing to quantify the relative contribution of temperature, salinity, and nutrients to the model's predictions (See US-3).
- **FR-005**: System MUST generate spatial visualization maps of prediction accuracy and feature importance for each ocean basin in the test set (See US-3).
- **FR-006**: System MUST enforce a memory limit of substantial RAM and a runtime limit of 6 hours for the entire analysis pipeline (See US-2).

### Key Entities

- **PhytoplanktonSample**: Represents a single measurement point, containing attributes for location (lat/lon), timestamp, chlorophyll-a concentration, and associated environmental drivers (temp, salinity, nutrients).
- **OceanBasin**: Represents a geographic region (e.g., North Atlantic, Pacific) used for data stratification and separate model evaluation.
- **ModelPerformance**: Represents the evaluation results of a model, containing metrics (RMSE, R², MAE) and the dataset split (train/val/test) used for calculation.

### Success Criteria

- **SC-001**: Predictive accuracy (R²) of the VLM model is measured against the baseline Random Forest model on the held-out test set to determine the magnitude of the difference. Success is defined as the system successfully quantifying whether the VLM R² exceeds the Baseline R² by a statistically significant margin (≥ 0.05) or not, using an appropriate statistical test (See US-2).
- **SC-002**: Computational feasibility is measured by ensuring the total pipeline runtime does not exceed a reasonable duration and peak memory usage does not exceed 7GB RAM on a standard GitHub Actions runner (See US-2).
- **SC-003**: Feature attribution validity is measured by confirming that the The sum of permutation importance scores for all drivers is normalized to unity within a tolerance of 0.01. (See US-3).
- **SC-004**: Data alignment quality is measured by the percentage of missing values in the final aligned dataset, which must be ≤ 5% (See US-1).
- **SC-005**: Model generalizability is measured by the variance in R² scores across different ocean basins; the system must report the difference between the highest and lowest basin R² (See US-2).

## Assumptions

- **Assumption about data availability**: The MODIS Aqua/Terra, SeaBASS, and BGC-Argo datasets contain sufficient temporal overlap (≥ 10 years) to support a robust train/validation/test split stratified by ocean basin.
- **Assumption about model architecture**: A pre-trained CLIP-based VLM with <500M parameters can be effectively fine-tuned on a CPU-only environment without requiring 8-bit quantization or GPU acceleration to achieve convergence, or a fallback to the baseline is available if convergence fails.
- **Assumption about environmental drivers**: Temperature, salinity, and nutrient data from reanalysis products are spatially and temporally aligned with satellite ocean color data, with any interpolation error quantified and validated against natural variability (See US-1).
- **Assumption about computational resources**: The GitHub Actions free-tier runner provides sufficient disk space (≥ 14GB) to store the preprocessed dataset and model checkpoints during the 6-hour execution window.
- **Assumption about statistical validity**: The relationship between environmental drivers and phytoplankton abundance is sufficiently captured by the selected features to allow for meaningful permutation importance analysis without severe multicollinearity masking effects.