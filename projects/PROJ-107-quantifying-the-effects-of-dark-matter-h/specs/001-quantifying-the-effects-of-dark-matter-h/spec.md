# Feature Specification: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation"

## User Scenarios & Testing

### User Story 1 - Core Data Ingestion and Halo Shape Computation (Priority: P1)

As a researcher, I need to download the IllustrisTNG-100 public data release and compute the triaxial shape parameters (axial ratios, triaxiality) for dark matter haloes using the reduced inertia tensor method, so that I can establish the foundational dataset for correlating geometry with galaxy properties.

**Why this priority**: Without accurate halo shape metrics, no subsequent analysis of galaxy formation can occur. This is the prerequisite data layer.

**Independent Test**: The system can be tested by verifying that the pipeline successfully retrieves the TNG-100 catalog, computes the inertia tensor for a random validation subset of [deferred] haloes, and outputs a CSV with valid axial ratios (0 < b/a ≤ 1, 0 < c/a ≤ 1) and triaxiality values (0 ≤ T ≤ 1). Specifically, verify that the output CSV contains no rows where b/a > 1 or c/a > 1, and that the count of processed haloes matches the input count minus excluded low-resolution haloes. This test validates the logic on a representative sample, while the full pipeline requirement (FR-001) mandates processing every FoF halo in the production run.

**Acceptance Scenarios**:

1. **Given** the IllustrisTNG-100 data URL is accessible, **When** the ingestion script runs, **Then** the halo and subhalo catalogs are downloaded and stored locally without corruption.
2. **Given** a set of dark matter particles within the virial radius, **When** the reduced inertia tensor is calculated, **Then** the resulting eigenvalues yield axial ratios and triaxiality parameters consistent with the method defined in the literature (e.g., `arxiv.org/abs/1907.11775v1`).
3. **Given** a halo with fewer than 10,000 dark matter particles, **When** the shape computation is attempted, **Then** the halo is flagged and excluded from the analysis to ensure resolution validity.

---

### User Story 2 - Statistical Correlation, Binning, and Mass Control (Priority: P2)

As a researcher, I need to bin haloes into prolate, triaxial, and spherical groups based on the c/a axial ratio, perform mass-matching to control for halo mass confounding, and execute statistical tests (Kruskal-Wallis, Mann-Whitney U, KS, and linear regression with mass control) to determine if galaxy properties (SFR, effective radius) differ significantly across these shape bins, so that I can quantify the relationship between halo geometry and galaxy formation.

**Why this priority**: This constitutes the primary scientific inquiry. It transforms raw data into statistical evidence regarding the research question while controlling for the critical confounder of halo mass.

**Independent Test**: The system can be tested by running the analysis on a subset of the data and verifying that the output includes correlation coefficients, p-values, regression coefficients, and a clear rejection or non-rejection of the null hypothesis for at least one galaxy property, with evidence of mass-matching or stratification.

**Acceptance Scenarios**:

1. **Given** the computed halo shapes and matched central galaxy properties, **When** the binning logic executes, **Then** haloes are correctly categorized into prolate (c/a < 0.5), triaxial (0.5 ≤ c/a ≤ 0.8), and spherical (c/a > 0.8) bins based on the c/a axial ratio.
2. **Given** the binned data, **When** mass-matching (stratification) is applied, **Then** haloes in each shape bin are paired or stratified by similar halo mass ranges to control for the mass-shape-galaxy confound.
3. **Given** the mass-matched data, **When** the Kruskal-Wallis H-test, Mann-Whitney U-tests, and Kolmogorov–Smirnov tests are applied, **Then** p-values are generated, and if p < 0.01, the null hypothesis of identical distributions is flagged as rejected.
4. **Given** the mass-matched data, **When** a linear regression of galaxy property ~ shape parameters controlling for halo mass is executed, **Then** the regression coefficients for shape parameters are reported with their confidence intervals.
5. **Given** multiple pairwise comparisons are performed, **When** the Mann-Whitney U-tests run, **Then** p-values are adjusted using Bonferroni correction to control the family-wise error rate.

---

### User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

As a researcher, I need to validate the findings by repeating the analysis on the Millennium-II dataset and warm-dark-matter variant snapshots, and performing a sensitivity sweep on the shape binning thresholds, so that I can ensure the results are not artifacts of a specific simulation or arbitrary cutoff choices.

**Why this priority**: This ensures the scientific rigor and generalizability of the findings, addressing the methodology panel's requirement for threshold justification and cross-validation.

**Independent Test**: The system can be tested by verifying that the sensitivity analysis produces a report showing how the significance of the correlation changes as the binning cutoffs are varied by ±0.05, and that results are compared across datasets.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the Millennium-II dataset is processed through the same pipeline, **Then** the correlation trends (direction and significance) are compared and reported as consistent or divergent.
2. **Given** the primary analysis results, **When** the warm-dark-matter variant snapshots are processed, **Then** the correlation trends are compared and reported as consistent or divergent.
3. **Given** the default shape cutoffs (0.5, 0.8), **When** the sensitivity analysis runs, **Then** the cutoffs are swept over the set {0.45, 0.55, 0.75, 0.85}, and the resulting variation in significance rates and p-value stability are tabulated (noting that false-positive rates cannot be calculated without ground truth).
4. **Given** the sensitivity analysis results, **When** the final report is generated, **Then** a conclusion is provided on whether the headline findings are robust to small variations in the shape definition.

---

### User Story 4 - Orientation Misalignment Analysis (Priority: P3)

As a researcher, I need to compute the orientation misalignment (angle between halo spin and galaxy spin, and halo major axis and galaxy major axis) and correlate these angles with galaxy properties, so that I can fully address the research question regarding halo shape and galaxy formation including orientation effects.

**Why this priority**: The research question explicitly includes 'orientation mis-alignment' as a key parameter. This analysis provides additional insight into the geometric relationship beyond simple shape bins.

**Independent Test**: The system can be tested by verifying that the pipeline outputs a CSV containing the computed misalignment angles (in degrees) and their correlation with galaxy properties.

**Acceptance Scenarios**:

1. **Given** the halo and galaxy particle data, **When** the spin vectors and major axes are computed, **Then** the angle between halo spin and galaxy spin, and halo major axis and galaxy major axis, are calculated for each matched pair.
2. **Given** the computed misalignment angles, **When** statistical tests are applied, **Then** the correlation between misalignment angle and galaxy properties (SFR, radius) is reported.

### Edge Cases

- What happens when the inertia tensor calculation yields a singular matrix (e.g., due to insufficient particle count or numerical precision errors)?
- How does the system handle haloes where the central galaxy is not the most massive subhalo (e.g., in merger scenarios)?
- What occurs if the TNG-100 API is temporarily unavailable or rate-limited during the download phase?
- How are outliers in star-formation rate (e.g., extreme starbursts) handled during the median calculation to prevent skewing the bin statistics?

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the reduced inertia tensor for dark matter particles within the virial radius for every FoF halo to derive axial ratios and triaxiality parameters (See US-1).
- **FR-002**: System MUST filter the dataset to exclude haloes with fewer than 10,000 dark matter particles to ensure resolution validity (See US-1).
- **FR-003**: System MUST categorize haloes into three distinct shape bins based on the c/a axial ratio: prolate (c/a < 0.5), triaxial (0.5 ≤ c/a ≤ 0.8), and spherical (c/a > 0.8) (See US-2).
- **FR-004**: System MUST perform non-parametric statistical testing (Kruskal-Wallis H-test, Mann-Whitney U-tests, and Kolmogorov–Smirnov tests) to compare galaxy property distributions across shape bins (See US-2).
- **FR-005**: System MUST apply Bonferroni correction to p-values when performing multiple pairwise comparisons to control the family-wise error rate (See US-2).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the shape binning thresholds over the set {0.45, 0.55, 0.75, 0.85} and report the variation in significance rates and p-value stability (See US-3).
- **FR-007**: System MUST repeat the full analysis pipeline on the Millennium-II dataset and warm-dark-matter variant snapshots to assess model dependence (See US-3).
- **FR-008**: System MUST include a metadata flag 'associational_only=true' in all output datasets to indicate the non-causal nature of the results (See US-2).
- **FR-009**: System MUST compute the orientation misalignment angles (between halo spin and galaxy spin, and halo major axis and galaxy major axis) for every matched halo-galaxy pair (See US-4).
- **FR-010**: System MUST correlate the computed misalignment angles with galaxy properties (SFR, effective radius) and report the results (See US-4).
- **FR-011**: System MUST perform linear regression of galaxy property ~ shape parameters controlling for halo mass (See US-2).
- **FR-012**: System MUST apply mass-matching or stratification to the shape bins before performing statistical comparisons to control for the confounding effect of halo mass (See US-2).

### Key Entities

- **Halo**: A dark matter structure identified in the simulation, characterized by mass, virial radius, and computed shape parameters (axial ratios, triaxiality).
- **Central Galaxy**: The most massive subhalo within a given Halo, characterized by stellar mass, star-formation rate, and effective radius.
- **Shape Bin**: A categorical grouping of Haloes based on their c/a axial ratio thresholds (Prolate, Triaxial, Spherical). This binning serves as a proxy for triaxiality.
- **Statistical Result**: A record containing the test statistic, p-value, and significance status for a specific comparison between Shape Bins and Galaxy Properties.
- **Misalignment Angle**: A quantitative measure of the angle (in degrees) between the halo spin/major axis and the galaxy spin/major axis.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Spearman correlation coefficient between halo triaxiality and galaxy star-formation rate is measured against the null hypothesis of zero correlation (See FR-004, US-2).
- **SC-002**: The p-value from the Kruskal-Wallis H-test is measured against a predetermined significance threshold to determine if galaxy property distributions differ across shape bins. (See FR-004, US-2).
- **SC-003**: The sensitivity of the significance result to threshold choice is measured by the variance of p-values across the swept threshold set {0.45, 0.55, 0.75, 0.85}; the variance must be ≤ 0.001 OR the significance rank order must be preserved (See FR-006, US-3).
- **SC-004**: The reproducibility metric is measured by comparing the direction and magnitude of the correlation coefficient between the IllustrisTNG-100 and Millennium-II datasets; correlation coefficients must differ by ≤ 0.1 in magnitude and share the same sign (See FR-007, US-3).
- **SC-005**: The computational feasibility is measured by ensuring the entire pipeline completes within a single GitHub Actions job on a runner with a limited number of CPU cores and constrained RAM. (See Assumptions).
- **SC-006**: The misalignment angle correlation is measured against the null hypothesis of zero correlation, with a significance threshold determined by standard statistical conventions. (See FR-010, US-4).

## Assumptions

- **Data Availability**: The IllustrisTNG-100 and Millennium-II public data releases are accessible via their respective URLs without requiring proprietary authentication or local hardware acceleration.
- **Computational Constraints**: The analysis will be performed on a CPU-only environment (GitHub Actions free tier) with ≤7 GB RAM; therefore, the dataset will be sampled or processed in chunks if it exceeds memory limits, and no GPU-accelerated libraries (e.g., PyTorch with CUDA) will be used.
- **Methodological Validity**: The reduced inertia tensor method using dark matter particles is a valid and standard proxy for the gravitational potential shape, as established in the referenced literature (e.g., `arxiv.org/abs/1907.11775v1`).
- **Associational Nature**: Since the data comes from cosmological simulations without random assignment of halo shapes, all conclusions drawn regarding the relationship between shape and galaxy properties will be strictly associational.
- **Threshold Justification**: The default binning thresholds (0.5, 0.8) are acknowledged as phenomenological cut-offs for a continuous variable, not physical definitions; the sensitivity analysis (FR-006) is required to validate their robustness.
- **Resolution Limit**: Haloes with <10,000 particles are assumed to have insufficient resolution for reliable shape estimation, and their exclusion will not introduce significant selection bias in the high-mass regime of interest.
- **Mass Confounding**: Halo mass is a strong confounder for both shape and galaxy properties; mass-matching or stratification is required to isolate the shape effect.