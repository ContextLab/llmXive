# Feature Specification: Fractal Dimension and Energy Dissipation in Turbulent Flows

**Feature Branch**: `001-fractal-dimension-turbulence`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Fractal Dimension and Energy Dissipation in Turbulent Flows"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fractal Dimension Computation (Priority: P1)

The researcher MUST be able to compute fractal dimensions of vorticity iso-surfaces from DNS velocity field data using a box-counting algorithm.

**Why this priority**: This is the core measurement capability without which the research question cannot be addressed. The fractal dimension is the primary predictor variable in the hypothesis.

**Independent Test**: Can be fully tested by running the box-counting algorithm on a synthetic Menger sponge (ground-truth D=2.73) and verifying the output D_f matches the ground truth within ±0.05.

**Acceptance Scenarios**:

1. **Given** a 512³ voxel velocity field at Re_λ = 200, **When** the box-counting algorithm identifies iso-surfaces at |ω| > threshold (configurable, default 3× global vorticity RMS), **Then** the fractal dimension D_f is computed and returned as a float with precision ≥ 0.01
2. **Given** a velocity field with uniform vorticity, **When** the algorithm runs, **Then** D_f ≤ 2.0 (planar structure) is returned
3. **Given** a velocity field with space-filling vorticity, **When** the algorithm runs, **Then** D_f ≥ 2.8 is returned

---

### User Story 2 - Energy Dissipation Rate Computation (Priority: P1)

The researcher MUST be able to compute local energy dissipation rate ε from the strain rate tensor derived from DNS velocity fields.

**Why this priority**: This is the outcome variable in the hypothesis. Without ε computation, no correlation analysis is possible.

**Independent Test**: Can be fully tested by running the dissipation computation on a Taylor-Green vortex analytical field and verifying the output ε values match the analytical solution within a relative error of ≤ 1%.

**Acceptance Scenarios**:

1. **Given** a velocity field with known kinematic viscosity ν, **When** the strain rate tensor S_ij is computed via central finite differences, **Then** ε = 2νS_ijS_ij is calculated for each voxel
2. **Given** a laminar flow field, **When** the algorithm runs, **Then** ε values are near-zero (≤ 10⁻⁶) across ≥ 95% of voxels
3. **Given** a turbulent flow field at Re_λ = 600, **When** the algorithm runs, **Then** ε values span ≥ 4 orders of magnitude (characteristic of turbulence intermittency)

---

### User Story 3 - Correlation Analysis and Statistical Testing (Priority: P2)

The researcher MUST be able to perform linear regression between D_f and log(ε) across spatial subdomains with bootstrap confidence intervals, ensuring statistical independence of samples.

**Why this priority**: This directly addresses the research question by quantifying the relationship. Without statistical testing, results remain qualitative.

**Independent Test**: Can be fully tested by running the correlation analysis on ≥ 100 samples separated by ≥ 10 integral length scales and verifying the Pearson correlation coefficient r and p-value are computed with p < 0.05 or p ≥ 0.05 clearly indicated.

**Acceptance Scenarios**:

1. **Given** ≥ 100 paired (D_f, ε) measurements from spatial subdomains separated by ≥ 10 integral length scales (λ), **When** linear regression is performed, **Then** Pearson r, p-value, and 95% confidence interval are returned for each thresholding method
2. **Given** n=1000 bootstrap resamples, **When** confidence intervals are computed, **Then** the CI width is ≤ 0.2 for |r| ≥ 0.5
3. **Given** multiple hypothesis tests across Reynolds numbers, **When** family-wise error is controlled, **Then** Bonferroni or Benjamini-Hochberg correction is applied

---

### User Story 4 - Reynolds Number Scaling Analysis (Priority: P3)

The researcher MUST be able to repeat the analysis across ≥ 3 Reynolds numbers (Re_λ = 200, 400, 600) and test for scaling laws, specifically testing the hypothesis that D_f is asymptotically constant vs. weakly dependent on Re_λ.

**Why this priority**: This extends the findings beyond a single flow condition, testing the generality of the relationship. Lower priority as it requires multiple datasets.

**Independent Test**: Can be fully tested by running the full pipeline on ≥ 3 Reynolds number datasets (Re_λ = 200, 400, 600) and verifying scaling exponent α is estimated with uncertainty bounds.

**Acceptance Scenarios**:

1. **Given** DNS datasets at Re_λ = 200, 400, 600, **When** the correlation analysis is repeated for each, **Then** D_f vs. Re_λ scaling is computed as D_f ~ Re_λ^α
2. **Given** α estimate from linear regression, **When** uncertainty is quantified, **Then** 95% CI for α is reported
3. **Given** no significant scaling (α ≈ 0 within CI), **When** results are reported, **Then** the null finding is explicitly stated

---

### User Story 5 - System Constraints and Resource Limits (Priority: P1)

The system MUST operate within strict resource constraints defined by the project constitution and available compute infrastructure, ensuring all analysis steps complete within allocated time and memory limits.

**Why this priority**: Without these constraints, the analysis may fail in the target CI/CD environment or exceed budgeted resources, rendering the feature non-functional in production.

**Independent Test**: Can be fully tested by running the full pipeline on a GitHub Actions standard Linux runner (2-core, 7GB RAM limit) and verifying peak memory ≤ 6 GB and total runtime ≤ 6 hours.

**Acceptance Scenarios**:

1. **Given** a 512³ DNS dataset, **When** the full analysis pipeline runs, **Then** peak memory usage (RSS) remains ≤ 6 GB
2. **Given** the full pipeline execution, **When** run on standard CI hardware, **Then** total runtime is ≤ 6 hours
3. **Given** a single analysis step, **When** executed, **Then** it completes within ≤ 30 minutes to comply with Constitution Section VII job segmentation

---

### Edge Cases

- What happens when the vorticity threshold for iso-surface identification is too high (no surfaces detected) or too low (space-filling surface)? The system MUST flag and reject such threshold values, requiring manual adjustment or defaulting to the configured range.
- How does the system handle DNS data files exceeding available memory (≥ 7 GB RAM)? The system MUST implement streaming/chunked processing to keep peak memory ≤ 6 GB (See US-5).
- What happens when bootstrap resampling fails to converge (e.g., due to small sample size)? The system MUST report this failure explicitly and require ≥ 100 samples as a minimum.
- How does the system handle Reynolds numbers outside the supported range (Re_λ < 200 or Re_λ > 600)? The system MUST log a warning and skip analysis for unsupported Re_λ values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download DNS velocity field data from the Johns Hopkins Turbulence Database (https://turbulence.pha.jhu.edu/) for isotropic turbulence at Re_λ = 200, 400, 600 (See US-1)
- **FR-002**: System MUST compute velocity gradient tensors ∇u from 3D velocity fields using central finite-difference schemes with precision ≥ double (See US-1)
- **FR-003**: System MUST compute fractal dimension using a vorticity threshold parameter, defaulting to a multiple of the global vorticity RMS (calculated over the entire 512³ field)., but allowing configuration for sensitivity analysis (See US-1)
- **FR-004**: System MUST calculate local energy dissipation rate ε = 2νS_ijS_ij using kinematic viscosity ν from the DNS metadata (See US-2)
- **FR-005**: System MUST perform Pearson correlation analysis between D_f and log(ε) with n ≥ 100 independent spatial subdomains, where independence is defined as subdomains separated by a minimum distance of 10 integral length scales (λ) (See US-3)
- **FR-006**: System MUST apply family-wise error correction (Bonferroni or Benjamini-Hochberg) when > 1 hypothesis test is conducted (See US-3)
- **FR-007**: System MUST execute all analysis on CPU-only with peak memory (RSS) ≤ 6 GB and total runtime ≤ 6 hours on a GitHub Actions standard Linux runner (2-core, 7GB RAM limit), with each analysis step wrapped in ≤30-minute GitHub Actions job segments to stay within the 6-hour total runtime constraint (See US-5)
- **FR-008**: System MUST perform sensitivity analysis on the vorticity threshold by sweeping threshold ∈ {×, 3×, 4× RMS} and report how D_f-ε correlation varies (See US-1)
- **FR-009**: System MUST verify correlation robustness by computing D_f-ε correlation across at least two distinct thresholding methods (e.g., normalized RMS vs. absolute vorticity) to decouple geometric complexity from energy magnitude and rule out mathematical identity artifacts (See US-3)

### Key Entities

- **VelocityField**: 3D array of u, v, w components with spatial coordinates; key attributes include dimensions (512³), Reynolds number Re_λ, and kinematic viscosity ν
- **VorticityIsoSurface**: Geometric structure defined by |ω| > threshold; key attributes include fractal dimension D_f, surface area, and threshold value
- **EnergyDissipationMap**: 3D array of ε values derived from strain rate tensor; key attributes include mean, variance, and intermittency ratio (ε_max/ε_mean)
- **CorrelationResult**: Statistical output from regression analysis; key attributes include Pearson r, p-value, 95% CI, and sample size n

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Fractal dimension D_f is measured against the physical constraint 2.0 ≤ D_f ≤ 3.0 (See US-1)
- **SC-002**: Energy dissipation rate ε is measured against the non-negativity constraint ε ≥ 0 and intermittency range ≥ 3 orders of magnitude (See US-2)
- **SC-003**: Pearson correlation coefficient r is measured against statistical significance threshold p < 0.05 with family-wise error correction applied (See US-3)
- **SC-004**: Sample size n is measured against the power requirement n ≥ 100 independent samples (See US-3)
- **SC-005**: Vorticity threshold sensitivity is measured by reporting correlation coefficient variation across threshold ∈ {2×, 3×, 4× RMS} (See US-1)
- **SC-006**: Computation resource usage is measured against the constraint peak memory ≤ 6 GB and runtime ≤ 6 hours (See US-5)
- **SC-007**: Correlation robustness is measured by comparing r values across distinct thresholding methods to ensure the relationship is not an artifact of a single normalization (See US-3)

## Assumptions

- The Johns Hopkins Turbulence Database provides isotropic turbulence DNS datasets at Re_λ = 200, 400, 600 with velocity gradient data accessible without authentication
- DNS data files fit within standard RAM allocations when loaded as numpy arrays; if larger, streaming/chunked processing will be implemented
- The box-counting algorithm can approximate fractal dimension for vorticity iso-surfaces with acceptable precision (±0.1) without requiring GPU acceleration
- The kinematic viscosity ν is available in the DNS metadata for each dataset and does not require external lookup
- All analysis is observational; findings will be framed as associational correlations, not causal relationships (no randomization in DNS data)
- The vorticity threshold of a multiple of RMS is a community-standard default for identifying coherent vortical structures in turbulence, but the correlation must be validated across multiple thresholds to avoid circularity
- The sample size of n = 100 spatial subdomains provides adequate statistical power for detecting |r| ≥ 0.3 with 80% power at α = 0.05
- No prior validation of the fractal dimension vs. energy dissipation relationship exists in the literature; this is an exploratory analysis
- The fractal dimension D_f may be asymptotically constant or weakly dependent on Re_λ; the analysis is designed to empirically test this specific hypothesis in the Re_λ = 200–600 range
- The available RAM limit is a hard constraint derived from the project constitution and available CI resources, necessitating chunked processing for large-scale grids.