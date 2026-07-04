# Feature Specification: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Feature Branch**: `001-solvent-effects`  
**Created**: 2026-05-17  
**Status**: Draft  
**Input**: User description: "Solvent Effects on Photo-Fries Rearrangement Kinetics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure and Execute Solvent Series (Priority: P1)

The researcher MUST be able to define a series of solvents spanning non-polar to polar conditions and initiate the experimental protocol for each condition with full environmental logging.

**Why this priority**: This is the foundational step. Without a controlled solvent series with documented environmental parameters, no kinetic data can be collected, and the research question cannot be addressed. It delivers the primary dataset.

**Independent Test**: Can be fully tested by configuring a solvent list (e.g., cyclohexane, methanol) and verifying the system logs the dielectric constant (validated against a versioned lookup table), temperature (25 ± 0.5°C), and relative humidity (±2% RH) for each run.

**Acceptance Scenarios**:

1. **Given** a list of 5+ solvents with known dielectric constants, **When** the researcher configures the experiment, **Then** the system records each solvent's properties by validating them against a versioned lookup table and prepares the instrument parameters.
2. **Given** a configured solvent series, **When** the researcher initiates the laser flash photolysis, **Then** the system captures transient-absorption data for the defined time range (sub-nanosecond to microsecond scales) with full environmental metadata.

---

### User Story 2 - Extract Radical-Pair Lifetime (Priority: P2)

The system MUST process the raw spectroscopic data to extract the singlet-radical-pair intermediate lifetime via global kinetic analysis with calibration validation.

**Why this priority**: This transforms raw data into the primary metric (lifetime) required to answer the research question. It is a distinct analytical step from data collection and must be reproducible.

**Independent Test**: Can be fully tested by uploading a set of decay traces and verifying the system outputs a lifetime value derived from exponential fitting with instrument calibration metadata.

**Acceptance Scenarios**:

1. **Given** raw decay traces from transient-absorption detection, **When** the system performs global kinetic analysis, **Then** it outputs a lifetime value with a confidence interval and calibration record.
2. **Given** multiple replicates (n ≥ 3) for a single solvent, **When** the analysis completes, **Then** the system calculates the mean and standard deviation of the lifetime and flags any replicate outliers beyond 2σ.

---

### User Story 3 - Correlate Solvation Energy with Kinetic Lifetimes (Priority: P3)

The researcher MUST be able to correlate computed solvation free energies with the experimentally determined lifetimes using associational inference framing.

**Why this priority**: This synthesizes the computational and experimental data to validate the hypothesis regarding solvent effects on radical-pair stability. It represents the final insight generation.

**Independent Test**: Can be fully tested by inputting solvation energy values and lifetime data, verifying the system generates a regression plot, statistical significance test, and multiple-comparison correction.

**Acceptance Scenarios**:

1. **Given** lifetime data for ≥5 solvent conditions and corresponding solvation free energies, **When** the correlation analysis is run, **Then** the system outputs a regression coefficient (R²) with p-value and multiple-comparison correction applied.
2. **Given** product distribution data from HPLC, **When** the statistical analysis is performed, **Then** the system confirms if trends meet statistical significance (p < 0.01) with family-wise error rate control.

---

### Edge Cases

- What happens when a solvent evaporates significantly during the measurement window, altering the dielectric constant? → System flags run and requires re-measurement.
- How does system handle photodegradation of the substrate if the laser pulse intensity is too high? → System monitors baseline absorbance drift and halts if >5% change detected.
- What happens when DFT computation fails for a specific solvent model? → System logs failure and proceeds with available data; marks correlation as partial.
- What happens when humidity control exceeds ±2% RH tolerance? → System pauses experiment and alerts researcher.
- How does system handle temperature excursions beyond 25 ± 0.5°C? → System flags affected data points for exclusion from primary analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow configuration of at least 5 distinct solvent conditions spanning a dielectric constant range of ε ≈ low to ε ≈ 33. (See US-1)
- **FR-002**: System MUST capture transient-absorption spectroscopy data in the UV to near-infrared wavelength range with ns–10 μs time resolution. (See US-1)
- **FR-003**: System MUST record environmental parameters for each run: temperature (25 ± 0.5°C), relative humidity (±2% RH), and barometric pressure. (See US-1)
- **FR-004**: System MUST perform global kinetic analysis on decay traces using exponential fitting to extract intermediate lifetimes with instrument calibration metadata. (See US-2)
- **FR-005**: System MUST integrate or accept computed solvation free energies from implicit solvent models (SMD/PCM) at DFT level (B3LYP/6-31G*) for ≤80% of conditions and explicit solvent models (QM/MM or cluster-continuum) for ≥20% of conditions. (See US-3)
- **FR-006**: System MUST perform statistical significance testing (ANOVA) across solvent conditions with support for n ≥ 3 replicates and multiple-comparison correction. (See US-3)
- **FR-007**: System MUST log all measured quantities per reproducibility standards: substrate mass, integration time per scan (ms), temperature, and instrument settings for each data point. (See US-2)

### Key Entities *(include if feature involves data)*

- **Solvent Condition**: Represents a specific solvent environment (Dielectric Constant, Temperature, Humidity, Volume, Barometric Pressure).
- **Kinetic Trace**: Represents the raw transient-absorption data for a specific solvent and time window with instrument calibration metadata.
- **Reaction Metric**: Represents the derived lifetime and product distribution values for a condition with confidence intervals and replicate statistics.
- **Calibration Record**: Represents instrument validation data for each measurement session (detector response, wavelength calibration, baseline stability).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Report R² with 95% confidence interval for the correlation between lifetime and solvation energy (measured against linear regression output). (See US-3)
- **SC-002**: Consistent trends observed across ≥5 solvent conditions (measured against solvent series configuration). (See US-1)
- **SC-003**: Perform significance testing and report exact p-value and family-wise error correction method (measured against ANOVA output). (See US-3)
- **SC-004**: Environmental parameters logged within tolerance for ≥95% of runs (measured against temperature ±0.5°C, humidity ±2% RH thresholds). (See US-1)
- **SC-005**: Report mean and standard deviation for n ≥ 3 replicates per solvent condition (measured against replicate analysis output). (See US-2)
- **SC-006**: All findings framed as associational (not causal) given observational design without random assignment. (See US-3)
- **SC-007**: Power analysis documented for sample size (n ≥ 3 per solvent); effect size estimation deferred to implementation phase. (See US-3)
- **SC-008**: Threshold sensitivity analysis performed for any decision cutoffs (e.g., lifetime discrepancy threshold ∈ {, 0.05, 0.1} ns) with reported variation in false-positive/false-negative rates. (See US-2)
- **SC-009**: Perform collinearity diagnostics (VIF analysis) to distinguish effects of dielectric constant and solvation energy if multiple predictors are used. (See US-3)
- **SC-010**: Logged dielectric constants match the versioned lookup table reference for ≥98% of configured solvents (measured against lookup table version hash). (See US-1)

### Methodological Soundness Requirements

- **SC-006**: All findings framed as associational (not causal) given observational design without random assignment. (See US-3)
- **SC-007**: Power analysis documented for sample size (n ≥ 3 per solvent); effect size estimation deferred to implementation phase. (See US-3)
- **SC-008**: Threshold sensitivity analysis performed for any decision cutoffs (e.g., lifetime discrepancy threshold ∈ {0.01, 0.05, 0.1} ns) with reported variation in false-positive/false-negative rates. (See US-2)
- **SC-009**: Perform collinearity diagnostics (VIF analysis) to distinguish effects of dielectric constant and solvation energy if multiple predictors are used. (See US-3)
- **SC-010**: Logged dielectric constants match the versioned lookup table reference for ≥98% of configured solvents (measured against lookup table version hash). (See US-1)

## Assumptions

- Substrate (e.g., phenyl benzoate) purity will be >99% as per standard esterification protocols.
- Temperature control will be maintained at 25 ± 0.5°C throughout all measurements.
- Relative humidity will be maintained at ±2% RH throughout all measurements to prevent hydration-state artifacts.
- Access to laser flash photolysis equipment with nanosecond resolution is available.
- Computational resources for B3LYP/6-31G* calculations are accessible.
- The analysis pipeline will run on CPU-only infrastructure (cores, ~7 GB RAM) for data processing; no GPU-accelerated methods are required.
- All solvents will be of analytical grade with documented water content to ensure consistent hydration states.
- Instrument calibration will be performed before each measurement session using certified reference standards.
- The relationship between solvent polarity and radical-pair lifetime is a hypothesis to be tested (potentially non-monotonic or null).
- Product distribution shifts toward ortho/para isomers in polar solvents, measurable via HPLC with UV detection.

## References

- [Learning Continuous Solvent Effects from Transient Flow Data: A Graph Neural Network Benchmark on Catechol Rearrangement (2025)](http://arxiv.org/abs/2512.19530v1)
- [Fluctuations and correlations in chemical reaction kinetics and population dynamics (2018)](http://arxiv.org/abs/1807.01248v1)
- [Erratum to the article: Charge transfer to solvent identified using dark channel fluorescence-yield L-edge spectroscopy, NATURE CHEMISTRY 2 (2010) 853 (2017)](http://arxiv.org/abs/1705.03941v2)
- [Enhancing Swelling Kinetics of pNIPAM Lyogels: The Role of Crosslinking, Copolymerization, and Solvent (2025)](http://arxiv.org/abs/2503.14134v2)
- [Guest Editorial: Special Topic on Data-enabled Theoretical Chemistry (2018)](http://arxiv.org/abs/1806.02690v2)