# Feature Specification: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Feature Branch**: `001-investigating-md-diffusion-predictive-power`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients"

## User Scenarios & Testing

### User Story 1 - Generate Timescale-Accuracy Curves for Simple Liquids (Priority: P1)

The researcher runs MD simulations for simple liquid systems (water, ethanol, acetone) at three specific timescales (1 ns, 5 ns, 10 ns), extracts Mean Squared Displacement (MSD) data, calculates diffusion coefficients, and compares them against experimental benchmarks to generate a timescale-accuracy curve.

**Why this priority**: This is the core scientific contribution of the project. Without the ability to generate the timescale-accuracy relationship, the research question remains unanswered. It represents the Minimum Viable Product (MVP) for the scientific inquiry.

**Independent Test**: The system can be fully tested by executing the simulation pipeline for a single solvent (e.g., water) across the three timescales, calculating the Mean Absolute Error (MAE) against the NIST reference value (at matching temperature), and producing a plot showing MAE vs. Simulation Duration.

**Acceptance Scenarios**:

1. **Given** a valid GROMACS/LAMMPS topology and coordinate file for water, **When** the system runs simulations at 1 ns, 5 ns, and 10 ns durations, **Then** it outputs diffusion coefficients for each duration with a calculated MAE against the NIST experimental value (at matching temperature).
2. **Given** the diffusion coefficients for water at three timescales, **When** the system generates the timescale-accuracy plot, **Then** the plot displays a clear trend line showing the relationship between simulation duration (x-axis) and prediction error (y-axis) with uncertainty bands derived from bootstrap resampling.

---

### User Story 2 - Validate Methodological Rigor via Sensitivity Analysis (Priority: P2)

The researcher verifies that the diffusion coefficient estimation is robust by performing a sensitivity analysis on the regression start time used to extract the diffusion coefficient from the MSD curve, ensuring the results are not artifacts of a specific cutoff choice.

**Why this priority**: Scientific validity requires that results are not dependent on arbitrary parameter choices. This step ensures the "timescale-accuracy" finding is robust and not a result of a specific, potentially biased, regression start time.

**Independent Test**: The system can be tested by re-running the diffusion calculation on a single 10 ns trajectory using three different regression start times (10%, 20%, 30% of the total trajectory length) and confirming that the resulting diffusion coefficients vary within a statistically acceptable range (e.g., < 5% deviation).

**Acceptance Scenarios**:

1. **Given** a completed 10 ns simulation trajectory for ethanol, **When** the system calculates the diffusion coefficient using three different regression start times (10%, 20%, 30% of the total trajectory length), **Then** the system reports the variance in the calculated diffusion coefficients and flags if the variance exceeds 5%.
2. **Given** the primary analysis results, **When** the system performs the sensitivity sweep, **Then** it outputs a sensitivity report confirming that the headline finding (accuracy improves with time) holds across the tested parameter range.

---

### User Story 3 - Execute Full Batch Analysis with Statistical Confidence Intervals (Priority: P3)

The researcher executes the full batch analysis across all three solvents (water, ethanol, acetone) and applies bootstrap resampling (1000 iterations, or 100 if time-constrained) to estimate 95% confidence intervals for the mean absolute error at each timescale.

**Why this priority**: This expands the scope from a single-case study to a generalizable finding across multiple chemical systems and provides the statistical rigor required to claim the results are significant rather than random noise.

**Independent Test**: The system can be tested by running the full pipeline for all three solvents and verifying that the final output includes a table or plot showing the MAE and 95% confidence intervals for each solvent at each timescale.

**Acceptance Scenarios**:

1. **Given** the completed simulations for water, ethanol, and acetone at 1, 5, and 10 ns, **When** the system performs 1000 bootstrap iterations on the error distribution (or 100 if the 6-hour limit is approached), **Then** it outputs a final summary table containing the Mean MAE and the 95% Confidence Interval for each solvent-timescale combination.
2. **Given** the statistical results, **When** the system generates the final report, **Then** it explicitly states whether the improvement in accuracy from 1 ns to 10 ns is statistically significant based on a bootstrap difference-of-means test (α ≤ 0.05).

### Edge Cases

- What happens if the simulation fails to equilibrate within the 1 ns window, resulting in a non-linear MSD curve? (System must detect non-linearity, flag the data point as invalid, and log a warning; the run is excluded from the "targeting three" set).
- How does the system handle experimental values that are missing for a specific solvent in the NIST dataset? (System must skip that specific solvent-timescale combination and log a warning, rather than crashing).
- What if the CPU time limit (6 hours) is exceeded during the bootstrap resampling phase? (System must reduce the number of bootstrap iterations to 100 to ensure completion within the 6-hour limit, while logging the reduction).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse experimental diffusion coefficients for water, ethanol, and acetone from the NIST Chemistry WebBook or OpenKIM to serve as ground truth, ensuring the experimental temperature matches the simulation temperature within ±1K. (See US-1)
- **FR-002**: System MUST execute MD simulations for each solvent targeting three specific durations: 1 ns, 5 ns, and 10 ns using a CPU-only backend (GROMACS or LAMMPS) without GPU acceleration, excluding any run that fails to equilibrate. (See US-1)
- **FR-003**: System MUST extract the Mean Squared Displacement (MSD) trajectory from each simulation and calculate the diffusion coefficient via linear regression of MSD vs. time. (See US-1)
- **FR-004**: System MUST perform bootstrap resampling with 1000 iterations to estimate 95% confidence intervals for the Mean Absolute Error (MAE) of the predictions, or 100 iterations if the wall-clock time exceeds 5.5 hours. (See US-3)
- **FR-005**: System MUST conduct a sensitivity analysis sweeping the regression start time over a range of {10%, 20%, 30%} of the total trajectory length to verify result robustness. (See US-2)
- **FR-006**: System MUST output a final report containing timescale-accuracy curves with uncertainty bands and a summary table of MAE and confidence intervals for all solvents. (See US-3)
- **FR-007**: System MUST utilize a coarse-grained force field (e.g., MARTINI) or a reduced system size to ensure simulations complete within the 6-hour runtime limit, applying necessary scaling factors for diffusion coefficients if compared to all-atom references. (See US-1)
- **FR-008**: System MUST validate the linearity of the MSD curve (R² ≥ 0.99) before calculating the diffusion coefficient; if the condition is not met, the system must flag the trajectory as invalid. (See US-1)

### Key Entities

- **Simulation Run**: Represents a single MD execution defined by solvent type, force field, and duration (1/5/10 ns).
- **Experimental Reference**: Represents the ground truth diffusion coefficient value sourced from NIST/OpenKIM for a specific solvent at a specific temperature.
- **Prediction Metric**: Represents the calculated diffusion coefficient and its associated error (MAE) relative to the reference.
- **Statistical Interval**: Represents the 95% confidence interval derived from bootstrap resampling for a specific prediction metric.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Mean Absolute Error (MAE) between MD-predicted and experimental diffusion coefficients is measured against the NIST reference values for water, ethanol, and acetone (at matching temperatures). (See US-1)
- **SC-002**: The 95% Confidence Interval width for the MAE is measured against the bootstrap distribution generated from 1000 iterations (or 100 iterations in fallback mode). (See US-3)
- **SC-003**: The variance in diffusion coefficients resulting from the sensitivity analysis (sweeping regression start time [deferred], [deferred], [deferred]) is measured against a 5% threshold to determine robustness. (See US-2)
- **SC-004**: The system completes the full batch analysis (simulations + post-processing) in ≤ 6 hours, regardless of whether the bootstrap iterations are 1000 or the fallback 100. (See US-1)
- **SC-005**: The statistical significance of the accuracy improvement from 1 ns to 10 ns is measured by a bootstrap difference-of-means test (p ≤ 0.05), rather than by checking for non-overlapping confidence intervals. (See US-3)

## Assumptions

- The NIST Chemistry WebBook or OpenKIM provides valid, accessible experimental diffusion coefficient data for water, ethanol, and acetone at specific temperatures (e.g., 298K or 300K) that can be matched to the simulation temperature.
- The coarse-grained force field (e.g., MARTINI) or reduced system size required by FR-007 can complete the necessary simulations within the 6-hour CI job limit on a 2-core runner, and valid scaling factors exist to compare these results to all-atom experimental references.
- The linear regression method for extracting diffusion coefficients from MSD curves is the standard approach and does not require GPU-accelerated machine learning alternatives for this dataset size.
- The simple liquid systems (water, ethanol, acetone) do not exhibit complex phase behaviors or aggregation that would prevent convergence within the 10 ns window, provided the system is coarse-grained or reduced as per FR-007.
- The bootstrap resampling (1000 iterations, or 100 in fallback) can be executed entirely in memory (RAM < 7 GB) without requiring disk swapping or external storage.
- The force field parameters (e.g., OPLS-AA, GROMOS, or MARTINI) required for these solvents are available in open-source repositories and are compatible with the chosen MD engine.