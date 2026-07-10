# Feature Specification: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Feature Branch**: `001-validity-equipartition-granular`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Validity of the Equipartition Theorem in Driven Granular Systems"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1)

As a researcher, I need to ingest particle tracking data and driving signal logs to compute translational kinetic, rotational, potential, and vibrational energy for every particle at every frame, so that I can establish the raw energy distribution baseline required for any statistical analysis.

**Why this priority**: This is the foundational step. Without accurate energy computation from raw kinematic data, no subsequent statistical tests or validity checks can be performed. It delivers the core dataset needed for the entire project.

**Independent Test**: Can be fully tested by running the ingestion script on a small, synthetic CSV subset with known velocities and positions, verifying that the calculated energy values match manual calculations within floating-point tolerance (1e-9).

**Acceptance Scenarios**:

1. **Given** a CSV file containing particle positions (x, y, z) and orientations (theta) at 100Hz, and a synchronized log of driving frequency, **When** the ingestion pipeline processes the data, **Then** the system outputs a dataframe where every row contains computed values for $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ derived from finite differences and standard physics formulas.
2. **Given** a dataset with missing frames in the video log, **When** the pipeline encounters the gap, **Then** it interpolates the position/orientation linearly to maintain time continuity or flags the specific time window for exclusion, ensuring no NaN values propagate to the energy calculation step.
3. **Given** a dataset where particle mass or moment of inertia varies by material type (steel vs. polymer), **When** the pipeline processes the data, **Then** it applies the correct material-specific physical constants from a configuration file to ensure energy units are consistent across all material groups.

---

### User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

As a researcher, I need to compare the observed energy distributions against the theoretical Maxwell-Boltzmann prediction using Kolmogorov-Smirnov tests and Chi-squared goodness-of-fit tests, so that I can determine if the system exhibits statistically significant violations of the equipartition theorem.

**Why this priority**: This is the core analytical step that directly answers the research question. It transforms raw energy data into a scientific conclusion regarding the validity of the theorem.

**Independent Test**: Can be fully tested by running the analysis module on a dataset pre-labeled as "thermal" (Maxwell-Boltzmann holds) and "non-thermal" (Maxwell-Boltzmann fails), verifying that the p-values and test statistics correctly classify the datasets according to the hypothesis.

**Acceptance Scenarios**:

1. **Given** binned energy data for a specific driving frequency (e.g., 10 Hz), **When** the statistical module runs, **Then** it outputs a p-value from a Kolmogorov-Smirnov test comparing the empirical distribution of energy components to the theoretical Maxwell-Boltzmann distribution, flagging the result as "significant" if $p < 0.01$.
2. **Given** the binned observed counts and expected counts derived from the Maxwell-Boltzmann PDF, **When** the system performs the chi-squared goodness-of-fit test, **Then** it reports a $\chi^2$ statistic and a boolean indicator of whether the null hypothesis (equipartition holds) is rejected at the 99% confidence level.
3. **Given** a dataset with multiple driving frequencies, **When** the system aggregates results, **Then** it generates a summary table showing the rejection rate of the equipartition hypothesis as a function of frequency, allowing for trend identification.

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

As a researcher, I need to perform a sensitivity analysis on the decision thresholds (e.g., the p-value cutoff or energy discrepancy tolerance) to ensure the findings are robust, so that the conclusions are not artifacts of arbitrary statistical choices.

**Why this priority**: This ensures methodological soundness and defensibility of the results. It addresses the "threshold justification" requirement, preventing the project from being blocked by the methodology panel for arbitrary cutoffs.

**Independent Test**: Can be fully tested by executing the sensitivity sweep script on a fixed dataset and verifying that the output report lists the variation in "false positive" or "rejection" rates across the specified threshold range (e.g., 0.01, 0.05, 0.10).

**Acceptance Scenarios**:

1. **Given** the primary statistical result (e.g., rejection of equipartition), **When** the sensitivity analysis runs, **Then** it sweeps the significance threshold $\alpha$ over the set $\{0.01, 0.05, 0.10\}$ and reports the corresponding change in the number of rejected null hypotheses.
2. **Given** a decision boundary for "quasi-thermal" behavior (e.g., energy ratio within 5% of 1.0), **When** the system runs the sensitivity check, **Then** it recalculates the classification rates using boundaries of $\{1\%, 5\%, 10\%\}$ and documents how the "quasi-thermal" regime size changes.
3. **Given** the requirement for multiple-comparison correction, **When** the system processes 10+ frequency bins, **Then** it applies a Benjamini-Hochberg (FDR) correction and outputs both the raw and corrected p-values to ensure family-wise error rate control.

---

### User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

As a researcher, I need to perform a linear regression to relate the magnitude of deviation from equipartition to driving frequency and material roughness, and test the significance of these relationships using t-tests, so that I can quantify the dependencies predicted by the research question.

**Why this priority**: This addresses the specific requirement in the original idea to "linear regression to relate deviations to driving frequency and material roughness; test significance with t-tests". It moves beyond simple binary rejection to quantifying the nature of the violation.

**Independent Test**: Can be fully tested by running the regression module on a synthetic dataset where the slope and intercept are known, verifying that the calculated coefficients and t-statistics match the expected values within a tolerance of 1%.

**Acceptance Scenarios**:

1. **Given** a dataset of deviation magnitudes (e.g., $\chi^2$ statistic or mean energy ratio difference) and corresponding driving frequencies, **When** the regression module runs, **Then** it fits a linear model and outputs the slope, intercept, and R-squared value.
2. **Given** the fitted regression model, **When** the system performs significance testing, **Then** it reports the t-statistic and p-value for the slope coefficient, determining if the relationship is significant at $p < 0.05$.
3. **Given** material properties (roughness proxy), **When** the system includes them as a predictor in the regression, **Then** it reports the coefficient significance and interaction effects between frequency and roughness.

---

### Edge Cases

- What happens when the particle tracking fails for >20% of frames in a specific time window? (System must exclude the window and log a warning, rather than crashing or producing biased averages).
- How does the system handle datasets where the driving frequency is not constant (chirped signals)? (System must bin by instantaneous frequency or exclude non-stationary segments).
- What occurs if the dataset lacks vertical (z-axis) position data, making potential energy calculation impossible? (System must flag the dataset as incomplete for potential energy analysis and proceed only with kinetic components).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest particle tracking CSVs and driving signal logs, synchronizing them by timestamp to align kinematic data with external forcing parameters (See US-1).
- **FR-002**: System MUST compute translational kinetic energy ($\frac{1}{2}mv^2$), rotational kinetic energy ($\frac{1}{2}I\omega^2$), potential energy ($mgz$), and vibrational energy components for every particle in every frame using finite-difference approximations for velocity and angular velocity (See US-1).
- **FR-003**: System MUST perform Kolmogorov-Smirnov tests to compare the empirical distribution of energy components against the theoretical Maxwell-Boltzmann distribution for each material and frequency bin, retaining the raw distribution data required for the test (See US-2).
- **FR-004**: System MUST calculate chi-squared goodness-of-fit statistics by comparing binned observed counts against expected counts derived from the Maxwell-Boltzmann PDF, and report significance for a default threshold of $p < 0.01$ (See US-2).
- **FR-005**: System MUST execute a sensitivity analysis sweeping significance thresholds ($\alpha \in \{0.01, 0.05, 0.10\}$) and discrepancy boundaries to report robustness of the rejection decisions (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction when testing across multiple frequency bins, with the default method being Benjamini-Hochberg (FDR) unless specified otherwise (See US-3).
- **FR-007**: System MUST perform linear regression to relate deviation magnitudes to driving frequency and material roughness, outputting slope, intercept, and R-squared values (See US-4).
- **FR-008**: System MUST test the significance of regression coefficients using t-tests and report the p-values for the slope parameters (See US-4).

### Key Entities

- **ParticleState**: Represents a single particle at a single time step, containing attributes: position (x, y, z), orientation (theta), velocity (v), angular velocity (omega), mass (m), and moment of inertia (I).
- **EnergySample**: Represents the raw energy values for a single particle at a single time step, containing attributes: $E_{trans}$, $E_{rot}$, $E_{pot}$, $E_{vib}$, and particle_id. This entity stores the raw distribution data required for KS tests.
- **EnergyDistribution**: Represents the aggregated energy statistics for a specific group (e.g., "Steel beads at 10Hz"), containing attributes: mean translational energy, mean rotational energy, mean potential energy, variance, and sample size.
- **StatisticalResult**: Represents the outcome of a hypothesis test, containing attributes: test_type (KS, Chi-Square, Regression), statistic_value, p_value, is_significant, and corrected_p_value.
- **RegressionResult**: Represents the outcome of a linear regression analysis, containing attributes: slope, intercept, r_squared, slope_p_value, and model_fit_quality.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of energy computation is measured against the ground-truth values derived from manual calculation on a synthetic test dataset (See US-1).
- **SC-002**: The validity of the statistical inference is measured against the known ground truth of the "thermal" vs "non-thermal" labeled test datasets to ensure correct rejection/acceptance rates (See US-2).
- **SC-003**: The robustness of the conclusions is measured by the boolean rejection decision (True/False) for the null hypothesis remaining identical across all thresholds in the set $\{0.01, 0.05, 0.10\}$ for the primary frequency bin (See US-3).
- **SC-004**: The methodological soundness is measured by the presence of a multiple-comparison correction in the final report, verified by checking that the reported p-values are adjusted for the number of frequency bins tested (See US-3).
- **SC-005**: The regression analysis validity is measured by the t-statistic significance (p < 0.05) of the slope coefficient relating deviation to driving frequency (See US-4).

## Assumptions

- The provided Zenodo and OpenGranular datasets contain sufficient frame rates (≥100 Hz) to accurately resolve particle velocities and angular velocities via finite differences without aliasing.
- The datasets include particle mass and material properties (density, radius) either explicitly or via metadata that allows for their derivation, as these are required for kinetic energy calculations.
- The driving signal logs are synchronized with the video timestamps within the dataset; the system assumes that phase-locked or high-order spline interpolation is sufficient to align the data, and any residual desynchronization error must not exceed 5% of the driving period to avoid invalidating the energy balance calculation.
- The analysis is strictly observational; therefore, all findings regarding energy distributions are framed as associational correlations with driving parameters, not causal claims of energy transfer mechanisms, unless the dataset explicitly includes randomized forcing protocols.
- The dataset size fits within the GitHub Actions runner constraints (≤7 GB RAM, ≤14 GB disk); if the raw dataset exceeds this, the system assumes a random sampling strategy (e.g., a configurable percentage of frames or particles) will be applied to fit the computational box without biasing the distribution shape.
- The "roughness" of particles is represented by a scalar parameter in the dataset or can be inferred from the material type (steel vs. glass vs. polymer); if a direct roughness metric is missing, the analysis assumes material type serves as a valid proxy for surface properties.