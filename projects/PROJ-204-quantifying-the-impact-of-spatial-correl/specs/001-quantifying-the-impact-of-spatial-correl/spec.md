# Feature Specification: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Feature Branch**: `001-quantify-spatial-correlations`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Spatial Correlations on Perovskite Solar Cell Efficiency"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

As a researcher, I need to automatically download, parse, and align publicly available EDS elemental maps (Pb, I, MA) and their corresponding device performance metrics (PCE, J_sc, V_oc) from the NREL Perovskite Database and Zenodo (hosting Materials Project metadata) so that I have a clean, unified dataset ready for spatial analysis.

**Why this priority**: Without a unified, aligned dataset, no spatial analysis can be performed. This is the foundational step that enables all subsequent statistical modeling.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script against a known subset of the public database and verifying that the output CSV contains exactly N rows (where N is the number of matched samples) with non-null values for all required columns (elemental maps, PCE, J_sc, V_oc).

**Acceptance Scenarios**:

1. **Given** a list of valid sample IDs from the NREL Perovskite Database, **When** the ingestion script runs, **Then** it downloads the corresponding EDS maps and performance metrics, aligns them to a common pixel grid, and outputs a unified CSV file with a high success rate of requested samples successfully processed.
2. **Given** an EDS map with defective regions (e.g., dead pixels or scan artifacts), **When** the pre-processing step runs, **Then** the script masks these regions and excludes them from the correlation calculation, logging the masked area percentage.
3. **Given** a sample where performance metrics are missing from the source, **When** the script runs, **Then** the sample is excluded from the final dataset, and a warning is logged with the specific sample ID.

---

### User Story 2 - Spatial Correlation Metric Extraction (Priority: P2)

As a physicist, I need to compute 2-D autocorrelation functions and Fourier transforms for each elemental map to extract specific correlation lengths (e.g., 1/e decay distance) and low-frequency spectral power metrics so that I can quantify the spatial ordering of the material.

**Why this priority**: This step transforms raw images into the quantitative predictor variables required to test the research hypothesis. It is the core analytical contribution of the project.

**Independent Test**: The extraction module can be tested independently by running it on synthetic test images with known correlation lengths (e.g., generated Gaussian noise with defined variance and correlation) and verifying that the calculated metrics match the ground truth within a tolerance of ±5%.

**Acceptance Scenarios**:

1. **Given** a calibrated 2-D elemental concentration map, **When** the analysis module runs, **Then** it computes the 2-D autocorrelation function and fits multiple decay models (exponential, Gaussian, power-law) to extract the correlation length, outputting the best-fit model and its parameters.
2. **Given** a set of elemental maps, **When** the Fourier analysis module runs, **Then** it calculates the integrated spectral power in the low-frequency band (starting from the zero-frequency limit up to 0.1 cycles/pixel) and outputs this as a secondary metric.
3. **Given** a map with insufficient resolution to determine a correlation length (e.g., autocorrelation does not decay within the image bounds), **When** the module runs, **Then** it flags the metric as "undefined" and records the maximum possible correlation length as a lower bound.

---

### User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

As a researcher, I need to fit linear regression models and calculate Pearson and Spearman correlation coefficients between the extracted spatial metrics and device PCE to determine if a statistically significant relationship exists, while applying multiple-comparison corrections and non-linear robustness checks.

**Why this priority**: This step directly answers the research question by quantifying the relationship between spatial ordering and efficiency. It provides the evidence needed to accept or reject the hypothesis.

**Independent Test**: The modeling module can be tested by running it on a synthetic dataset with a known negative correlation (r = -0.6) and verifying that the model detects a statistically significant relationship (p < 0.05) after applying the specified correction.

**Acceptance Scenarios**:

1. **Given** a dataframe of correlation lengths and PCE values, **When** the statistical model runs, **Then** it calculates the Pearson and Spearman correlation coefficients (r) and p-values, and outputs the result with a flag indicating significance at the standard convention α = 0.05.
2. **Given** multiple hypothesis tests (e.g., testing correlation for Pb, I, and MA separately), **When** the analysis runs, **Then** it applies a Benjamini-Hochberg correction for false discovery rate and reports both raw and adjusted p-values.
3. **Given** a dataset with a potential outlier, **When** the robustness check runs, **Then** it performs leave-one-out cross-validation and reports the change in the correlation coefficient (Δr) when each sample is removed, ensuring the result is not driven by a single point.
4. **Given** a dataset, **When** the co-location validation runs, **Then** it verifies that the EDS map and PCE value originate from the same physical device or a validated representative sample, flagging any mismatch.

### Edge Cases

- What happens if the downloaded EDS maps have different pixel dimensions or aspect ratios? (Handled by resampling to a common grid in US-1).
- How does the system handle samples where the autocorrelation function does not decay to 1/e within the image bounds? (Handled by flagging as "undefined" in US-2).
- What if the dataset contains fewer than 30 samples, making statistical power low? (Handled by reporting power limitations in the final output, as per methodology constraints).
- How does the system handle missing values in the performance metrics for a matched sample? (Handled by excluding the sample in US-1).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download EDS maps from the NREL Perovskite Database and Zenodo (hosting Materials Project metadata), aligning them to a common pixel grid, to ensure data consistency. If EDS maps are unavailable in the primary source, the system MUST attempt to retrieve metadata from the Materials Project API as a fallback, but must flag the sample as 'incomplete' if no EDS data is found (See US-1).
- **FR-002**: System MUST compute 2-D autocorrelation functions for each elemental map and fit multiple decay models (exponential, Gaussian, power-law) to extract the correlation length, selecting the best-fit model via AIC and providing a quantitative measure of spatial ordering (See US-2).
- **FR-003**: System MUST perform 2-D Fourier transforms on elemental maps to calculate integrated spectral power in the low-frequency band (0 to 0.1 cycles/pixel) as an alternative spatial metric (See US-2).
- **FR-004**: System MUST calculate Pearson and Spearman correlation coefficients and p-values between extracted spatial metrics and device PCE, applying Benjamini-Hochberg correction for multiple comparisons to control the false discovery rate. The system MUST also fit a Generalized Additive Model (GAM) to detect non-linear relationships (See US-3).
- **FR-005**: System MUST perform leave-one-out cross-validation to assess the robustness of the correlation results against outliers, reporting the change in correlation coefficient (Δr) for each iteration (See US-3).
- **FR-006**: System MUST generate a summary report containing the correlation coefficients, p-values, robustness metrics, and sample count in CSV and PDF formats. The report MUST include fields: 'correlation coefficient', 'p-value', 'sample count', 'best-fit decay model', 'AIC score', and 'Δr max' (See US-3).
- **FR-007**: System MUST perform a co-location validation step to verify that the EDS map and PCE value originate from the same physical device or a validated representative sample, flagging any mismatch for exclusion (See US-3).
- **FR-008**: System MUST flag samples where bulk-averaged EDS maps are correlated with surface-dominated PCE metrics without depth-resolved validation, and must optionally exclude them if a sensitivity analysis indicates high sensitivity to this confounding variable (See Assumptions).

### Key Entities

- **ElementalMap**: Represents a 2-D grid of concentration values for a specific element (Pb, I, MA) within a perovskite film, including metadata on pixel size and spatial resolution.
- **DevicePerformance**: Represents the power-conversion efficiency (PCE), short-circuit current (J_sc), and open-circuit voltage (V_oc) for a specific perovskite solar cell device.
- **SpatialMetric**: Represents a derived quantitative value describing the spatial ordering of an elemental map, including correlation length and low-frequency spectral power.
- **AnalysisResult**: Represents the outcome of the statistical modeling, including correlation coefficients, p-values, and robustness metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation length extraction accuracy is measured against synthetic test images with known ground-truth correlation lengths, targeting a deviation of ≤5% (See US-2).
- **SC-002**: The statistical calculation logic is measured against a reference implementation (e.g., SciPy stats module), requiring p-values to match within a numerical tolerance of ±0.001. The research significance threshold (α) is a deferred parameter (See US-3).
- **SC-003**: The robustness of the correlation result is measured by the correct calculation and reporting of Δr values during leave-one-out cross-validation (See US-3).
- **SC-004**: The data ingestion success rate is measured against the total number of requested samples, requiring a success rate consistent with project constraints [deferred] (See US-1).

## Assumptions

- The NREL Perovskite Database and Zenodo (hosting Materials Project metadata) will remain publicly accessible and provide EDS maps with sufficient resolution (≥512x512 pixels) to calculate correlation lengths within the download limit.
- The available dataset contains at least 30 matched samples (EDS maps + performance metrics) to provide adequate statistical power for correlation analysis; if fewer samples are available, the study will report this as a power limitation.
- The elemental composition maps (Pb, I, MA) are representative of the entire active layer and not just surface features, allowing for valid inference about bulk charge-carrier diffusion. *Note: This assumption is limited by EDS depth resolution; FR-008 addresses this by flagging potential confounding variables.*
- The relationship between spatial correlation length and PCE is linear or monotonic, justifying the use of Pearson correlation and linear regression models. *Note: FR-004 adds non-parametric (Spearman) and non-linear (GAM) checks to mitigate this risk.*
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to process the ≤200 MB dataset and run the Python analysis scripts within the 6-hour time limit.
- The "1/e" decay point is an appropriate and standard metric for defining correlation length in this context, consistent with literature on material heterogeneity. *Note: FR-002 extends this to include Gaussian and power-law models to ensure robustness.*
- The specific success rate threshold for data ingestion (e.g., ≥95%) and the significance level (α) are deferred to the implementation phase as project-level constraints.