# Feature Specification: Statistical Analysis of Publicly Available Climate Model Output Ensembles

**Feature Branch**: `001-climate-fPCA-robustness`  
**Created**: 2026-07-19  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Climate Model Output Ensembles"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Functional Representation (Priority: P1)

The system must successfully ingest raw CMIP6 ensemble data for temperature and precipitation, preprocess missing values, and transform discrete time-series grid points into smooth continuous functions using B-spline basis expansion.

**Why this priority**: This is the foundational step. Without a valid functional representation of the data, no subsequent statistical analysis (fPCA) can occur. It delivers the primary value of converting raw, high-dimensional climate output into a statistically tractable format.

**Independent Test**: Can be fully tested by running the ingestion and smoothing pipeline on a small, fixed subset of CMIP6 models and verifying that the resulting B-spline coefficients are generated without error and that the reconstructed curves match the original data within a defined tolerance.

**Acceptance Scenarios**:

1. **Given** a set of CMIP6 model output files for global land temperature, **When** the ingestion script processes them, **Then** missing values are linearly interpolated, and a B-spline basis expansion (10-20 basis functions) is generated for each ensemble member.
2. **Given** the generated B-spline coefficients, **When** the data is reconstructed, **Then** the mean squared error between the original data points and the reconstructed function is ≤ 0.01 (normalized).
3. **Given** a dataset with >10% missing time steps, **When** the preprocessing runs, **Then** the system flags the specific time steps and models affected in a log file without crashing.

---

### User Story 2 - Dominant Mode Extraction via fPCA (Priority: P2)

The system must perform Functional Principal Component Analysis (fPCA) on the smoothed data to identify the dominant modes of spatiotemporal variability and calculate the cumulative variance explained by each component.

**Why this priority**: This addresses the core research question regarding "what are the dominant modes." It is the primary analytical engine of the project.

**Independent Test**: Can be tested by executing the fPCA algorithm on the prepared data and verifying that the output includes a sorted list of eigenvalues, corresponding eigenfunctions (modes), and cumulative variance percentages.

**Acceptance Scenarios**:

1. **Given** the functional data representation, **When** fPCA is executed, **Then** the system outputs at least 3 dominant functional principal components.
2. **Given** the eigenvalues from fPCA, **When** cumulative variance is calculated, **Then** the first 3-5 components explain ≥ 80% of the total ensemble variance.
3. **Given** the eigenfunctions, **When** visualized, **Then** they represent distinct spatiotemporal patterns (e.g., global warming trends, ENSO-like oscillations) that differ from simple scalar averages.

---

### User Story 3 - Robustness Assessment via Bootstrap Resampling (Priority: P3)

The system must assess the stability of the identified dominant modes and trend projections by repeatedly performing fPCA on random subsamples of the ensemble members (bootstrap resampling) and comparing the results.

**Why this priority**: This addresses the "how robust" aspect of the research question. It validates whether the findings are driven by the entire ensemble or specific model families.

**Independent Test**: Can be tested by running the bootstrap loop (100 iterations), calculating the correlation or distance between the principal components of each subsample and the full-sample components, and reporting the stability metrics.

**Acceptance Scenarios**:

1. **Given** the full ensemble fPCA results, **When** 100 bootstrap subsamples are generated and analyzed, **Then** the system calculates a stability metric (e.g., correlation of loadings) for each dominant component.
2. **Given** the stability metrics, **When** a histogram is generated, **Then** the distribution shows a clear peak indicating consistent mode identification across subsamples.
3. **Given** a specific mode that shows low stability (high variance in loadings), **When** the system flags it, **Then** the output includes a list of the specific ensemble members whose removal caused the instability.

---

### Edge Cases

- What happens when the CMIP6 dataset contains models with significantly different time resolutions or grid structures? (System must resample to a common grid/time step or skip with a warning).
- How does the system handle a scenario where the ensemble size is too small for meaningful bootstrap resampling (e.g., < 10 models)? (System must halt and report an error regarding statistical power).
- What happens if the B-spline basis expansion fails to converge for a specific model due to extreme outliers? (System must exclude that specific model and log the reason).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest CMIP6 data for near-surface temperature and precipitation, handle missing values via linear interpolation, and standardize across ensemble members. (See US-1)
- **FR-002**: System MUST represent each ensemble member as a smooth function using B-spline basis expansion with 10-20 basis functions to capture spatiotemporal continuity. (See US-1)
- **FR-003**: System MUST execute Functional Principal Component Analysis (fPCA) to extract dominant modes of variability and compute the cumulative variance explained by each component. (See US-2)
- **FR-004**: System MUST perform bootstrap resampling of ensemble members (≥ 100 iterations) to generate subsamples for robustness testing. (See US-3)
- **FR-005**: System MUST calculate and report stability metrics (e.g., loading correlations) comparing fPCA results from subsamples against the full ensemble results. (See US-3)
- **FR-006**: System MUST perform a permutation test (≥ 1000 permutations) to determine the statistical significance of the extracted eigenvalues. (See US-2)
- **FR-007**: System MUST output visualizations of the dominant modes as spatiotemporal patterns with uncertainty bands derived from the bootstrap resampling. (See US-3)

### Key Entities

- **Functional Ensemble Member**: A continuous mathematical function representing the spatiotemporal evolution of a specific climate model's output (Temperature/Precipitation) over time.
- **Dominant Mode (Eigenfunction)**: A spatial-temporal pattern extracted by fPCA that represents a primary source of variability within the ensemble.
- **Bootstrap Subsample**: A random subset of the original ensemble members used to test the stability of the analysis results.
- **Stability Metric**: A quantitative measure (e.g., correlation coefficient) indicating how consistent a specific mode is across different bootstrap iterations.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The cumulative variance explained by the first 3-5 functional principal components is measured against the total ensemble variance to confirm ≥ 80% retention. (See FR-003)
- **SC-002**: The stability of dominant modes is measured by the correlation of eigenfunction loadings across 100 bootstrap iterations, with a target mean correlation ≥ 0.90 for robust modes. (See FR-005)
- **SC-003**: The statistical significance of eigenvalues is measured against a null distribution generated by 1000 permutation tests, requiring a p-value < 0.05 for retained components. (See FR-006)
- **SC-004**: The computational runtime and memory usage are measured against the GitHub Actions free-tier limits (2 CPU, 7 GB RAM, 6 hours) to ensure feasibility. (See FR-001, FR-004)
- **SC-005**: The information gain of fPCA over traditional scalar summaries is measured by comparing the variance captured by the functional approach versus the variance captured by simple mean/variance statistics. (See US-2)

## Assumptions

- **Data Availability**: The CMIP6 dataset selected for analysis contains sufficient temporal coverage (historical + scenario runs) and spatial resolution to support B-spline basis expansion without excessive interpolation artifacts.
- **Methodological Framing**: Since the analysis is observational (no random assignment of models), all findings regarding "dominant modes" and "robustness" are framed as associational patterns within the ensemble, not causal claims about the climate system.
- **Computational Constraints**: The analysis will use a CPU-tractable approximation of fPCA (e.g., using `scikit-fda` or `refund` on sampled data) and will not require GPU acceleration or 8-bit quantization, ensuring it fits within the 2 CPU / 7 GB RAM / 6-hour GitHub Actions free-tier limits.
- **Model Similarity**: The ensemble members selected are assumed to be distinct enough that bootstrap resampling effectively simulates the removal of specific model families; if model similarity is too high, the robustness test may be conservative.
- **Threshold Justification**: The decision to retain 3-5 components is based on the community standard of capturing ≥ 80% of variance; a sensitivity analysis will sweep the retention threshold (e.g., 70%, 80%, 90%) to verify stability.
- **Variable Fit**: The CMIP6 variables (temperature, precipitation) are assumed to contain all necessary information to represent the dominant modes of variability; no external covariates (e.g., aerosol forcing data) are required for this specific analysis.
