# Feature Specification: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Feature Branch**: `001-investigate-equipartition-granular-systems`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Validity of the Equipartition Theorem in Driven Granular Systems"

## User Scenarios & Testing

### User Story 1 - Energy Component Extraction and Aggregation (Priority: P1)

The research pipeline must ingest raw particle tracking data (positions, orientations) and driving signal logs, then compute and aggregate the primary energy components (translational kinetic and rotational kinetic) for every particle at every time step, binned by driving frequency and material type. Potential energy is calculated for diagnostic purposes but excluded from the equipartition ratio test.

**Why this priority**: This is the foundational data transformation step. Without accurate extraction of $E_{trans}$ and $E_{rot}$, no statistical comparison to the equipartition theorem is possible. It represents the core "data acquisition and processing" phase of the methodology.

**Independent Test**: Can be fully tested by running the pipeline on a small, synthetic CSV dataset with known kinematic properties and verifying that the output JSON/CSV contains the exact calculated energy values for each particle frame.

**Acceptance Scenarios**:

1. **Given** a CSV file containing particle positions (x, y, z) and orientations (theta) for steel beads at 10Hz, **When** the pipeline processes the file, **Then** the output must contain a row for each particle-frame with calculated $E_{trans} = 0.5 \cdot m \cdot v^2$ and $E_{rot} = 0.5 \cdot I \cdot \omega^2$.
2. **Given** multiple input files with different driving frequencies (5Hz, 10Hz, 15Hz), **When** the aggregation step runs, **Then** the resulting dataset must include a `frequency_bin` column correctly grouping the data into 5Hz intervals.
3. **Given** a dataset where the driving signal log is missing, **When** the pipeline attempts to synchronize, **Then** the system must halt with a clear error indicating the missing synchronization source rather than proceeding with null values.
4. **Given** a dataset where the particle mass is not explicitly provided in the metadata, **When** the pipeline processes the file, **Then** the system must attempt to derive mass from the material type and a default radius of a moderate magnitude, or fail with a specific error if derivation is impossible.

---

### User Story 2 - Statistical Deviation Analysis (Priority: P2)

The system must compare the observed mean energy values against the theoretical equipartition prediction (equal mean energy per degree of freedom) using Two-Sample t-tests and ANOVA, generating a report of p-values and deviation metrics for each frequency/material bin. Additionally, the system must perform a linear regression to relate deviations to driving frequency and material type.

**Why this priority**: This implements the core "Statistical assessment" logic required to answer the research question. It transforms raw energy values into the statistical evidence needed to accept or reject the hypothesis.

**Independent Test**: Can be fully tested by feeding the pipeline a dataset constructed to perfectly match equipartition (equal mean energy per degree of freedom) and verifying that the t-test returns $p > 0.05$, and a dataset with known bias returns $p < 0.01$.

**Acceptance Scenarios**:

1. **Given** a dataset of energy means for glass beads at 10Hz, **When** the statistical assessment module runs, **Then** it must output a t-test statistic and p-value comparing the mean translational energy to the mean rotational energy.
2. **Given** a dataset where the mean translational energy is 2x the mean rotational energy, **When** the t-test runs, **Then** the resulting p-value must be $< 0.01$ to flag a statistically significant deviation.
3. **Given** multiple hypothesis tests across different frequency bins, **When** the analysis completes, **Then** the output must include a Holm-Bonferroni-corrected p-value to account for multiple comparisons.

---

### User Story 3 - Sensitivity Analysis of Thresholds (Priority: P3)

The system must perform a sensitivity analysis on the significance threshold ($\alpha$) by sweeping the cutoff value over the set $\{0.01, 0.05, 0.10\}$ and reporting the count of frequency bins classified as "significant deviation" for each threshold in a summary table.

**Why this priority**: This ensures methodological soundness by preventing the results from being artifacts of an arbitrarily chosen significance threshold. It satisfies the requirement for threshold justification and sensitivity.

**Independent Test**: Can be fully tested by running the analysis with a fixed dataset and three different p-value thresholds, verifying that the output table correctly reflects the changing counts of "deviation detected" vs. "no deviation" across the sweep.

**Acceptance Scenarios**:

1. **Given** a fixed dataset of energy ratios, **When** the sensitivity analysis runs with thresholds $\{0.01, 0.05, 0.10\}$, **Then** the output must contain a summary table showing the number of frequency bins classified as "significant deviation" for each threshold.
2. **Given** a result where the p-value is exactly 0.04, **When** the sensitivity analysis is performed, **Then** the system must correctly classify this as "significant" at $\alpha=0.05$ but "non-significant" at $\alpha=0.01$.
3. **Given** a dataset where the deviation is marginal, **When** the sensitivity analysis runs, **Then** the report must explicitly state the "stability" of the conclusion (i.e., whether the conclusion changes across the swept thresholds).

---

### Edge Cases

- What happens when the particle tracking data has gaps (missing frames) that prevent accurate velocity calculation via finite differences? (System must interpolate or flag the particle as invalid for that frame).
- How does the system handle datasets where the particle mass is not explicitly provided in the metadata? (System must derive mass from material type and a default radius of a standard magnitude, or fail with a specific error).
- How does the system handle a driving frequency of 0 Hz (static case) where kinetic energy should theoretically be zero? (System must exclude these bins from the equipartition ratio calculation to avoid division by zero).

## Requirements

### Functional Requirements

- **FR-001**: System MUST calculate translational kinetic energy ($0.5 \cdot m \cdot v^2$) and rotational kinetic energy ($0.5 \cdot I \cdot \omega^2$) for every particle in every frame using finite-difference derivatives for velocity and angular velocity. Potential energy ($m \cdot g \cdot z$) MUST be calculated for diagnostic purposes but excluded from the equipartition ratio test. (See US-1)
- **FR-002**: System MUST synchronize particle tracking timestamps with external driving signal logs (frequency/amplitude) and bin the resulting energy data into 5Hz intervals for frequency analysis. (See US-1)
- **FR-003**: System MUST perform Two-Sample t-tests to compare the mean translational energy to the mean rotational energy (testing the null hypothesis of a 1:1 ratio) and ANOVA for multi-group comparisons across material types. (See US-2)
- **FR-004**: System MUST apply the Holm-Bonferroni method to all p-values generated across multiple frequency bins and material types to control family-wise error rate. (See US-2)
- **FR-005**: System MUST execute a sensitivity analysis that sweeps the significance threshold ($\alpha$) over the set $\{0.01, 0.05, 0.10\}$ and outputs a summary table showing the count of frequency bins classified as having significant deviation for each threshold. (See US-3)
- **FR-006**: System MUST validate that input datasets contain all required columns (position x/y/z, orientation, timestamp) and, if particle mass is missing, MUST derive mass using the standard formula for a solid sphere assuming a default radius of a standard magnitude based on material type metadata, or fail with a specific error if derivation is impossible. (See US-1)
- **FR-007**: System MUST perform a linear regression analysis relating the magnitude of energy deviation (difference between mean translational and rotational energy) to driving frequency and material type, and MUST test the significance of the regression coefficients using t-tests. (See US-2)

### Key Entities

- **ParticleFrame**: Represents a single particle at a specific timestamp; attributes include position, orientation, calculated velocities, and three energy values (trans, rot, pot).
- **EnergyBin**: Represents an aggregation of ParticleFrames grouped by driving frequency and material type; attributes include mean energy, variance, and statistical test results.
- **StatisticalResult**: Represents the output of a hypothesis test; attributes include test type (t-test, ANOVA, Regression), statistic value, raw p-value, and corrected p-value.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The deviation of observed energy ratios from the equipartition prediction is measured against the theoretical expectation of equal mean energy per degree of freedom (1:1 ratio for translational vs. rotational energy only; potential energy is excluded). (See FR-003)
- **SC-002**: The statistical significance of the observed deviations is measured against the corrected p-value threshold derived from the Holm-Bonferroni method (FR-004) and the regression coefficient significance (FR-007). (See FR-003, FR-004, FR-007)
- **SC-003**: The robustness of the "significant deviation" classification is measured against the sensitivity analysis sweep across $\alpha \in \{0.01, 0.05, 0.10\}$. (See FR-005)
- **SC-004**: The computational feasibility is measured against the constraint of completing the full analysis (data ingestion, energy calculation, statistical testing, and visualization) within 6 hours on a CPU-only runner with ≤7 GB RAM, processing a dataset of ≥ 1,000,000 frames. (See Assumptions)

## Assumptions

- The publicly available "Granular experiment dataset" (Zenodo) and "OpenGranular" (OpenML ID: 98765) contain the necessary variables (particle mass, moment of inertia, position, orientation, and driving frequency) to compute all three energy components. If the dataset lacks explicit moment of inertia ($I$) or particle radius, the system will derive $I$ using the standard formula for a solid sphere ($I = \frac{2}{5}mr^2$) assuming a default radius of 2.5mm based on material type metadata, as specified in FR-006.
- The analysis assumes the driving signal is perfectly periodic and the frequency bins (5Hz) align with the experimental design; if the data contains transient startup phases, these will be excluded from the steady-state analysis.
- The system assumes a standard gravitational acceleration ($g = 9.81 m/s^2$) and that the vertical displacement ($z$) is calibrated correctly in the provided video tracking data.
- The analysis is observational; therefore, any findings regarding the relationship between driving frequency and energy distribution will be framed as associational rather than causal, as there is no random assignment of particles to frequency states.
- The dataset size is assumed to be small enough (after sampling if necessary) to fit entirely within 7 GB of RAM, avoiding the need for out-of-core processing or database storage.
- The "roughness" of particles is treated as a categorical variable (material type) as a proxy, assuming the provided datasets do not have a direct quantitative roughness metric.
- The analysis will use standard double-precision floating-point arithmetic, as the CPU-only environment does not support mixed-precision or GPU-accelerated libraries.
- Potential energy is excluded from the equipartition ratio test (1:1) as it is not a quadratic degree of freedom in this specific driven granular context.