# Specification: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## 1. Introduction
This project investigates the accuracy of Molecular Dynamics (MD) simulations in predicting self-diffusion coefficients for simple liquids (water, ethanol, acetone) across varying timescales.

## 2. User Stories
- **US1**: As a researcher, I want to generate timescale-accuracy curves for simple liquids so that I can assess convergence.
- **US2**: As a researcher, I want to validate methodological rigor via sensitivity analysis so that I can confirm robustness.
- **US3**: As a researcher, I want to execute full batch analysis with statistical confidence intervals so that I can report on trends.

## 3. Functional Requirements
- **FR-001**: System must load experimental diffusion coefficients from `data/raw/nist_refs.json`.
- **FR-004**: Bootstrap resampling must use 1000 iterations, with a fallback to 100 if wall-clock time exceeds 5.5 hours.
- **FR-007**: Simulations must use MARTINI force field or reduced system size to meet runtime limits.
- **FR-008**: The R² threshold for validating linear MSD trajectories must be 0.95.

## 4. Assumptions
- Experimental data is manually curated and stored in `data/raw/nist_refs.json` because NIST does not provide a programmatic API for this specific dataset.
- The MARTINI force field provides sufficient accuracy for the relative comparisons required by this study.

## 5. Success Criteria
- **SC-001**: Timescale-accuracy curves (MAE vs. Duration) are generated for all solvents.
- **SC-002**: Sensitivity analysis confirms variance in D values < 5% across start times (0.1, 0.2, 0.3).
- **SC-003**: Bootstrap confidence intervals (95%) are calculated for MAE estimates.
- **SC-004**: Summary tables include mean MAE, 95% CI, and descriptive trend analysis.
- **SC-005**: The study performs **descriptive trend analysis** and a **CI overlap check** (comparing 1ns vs 10ns intervals) to assess improvement. **Explicitly, the study does NOT perform a bootstrap difference-of-means test (p-value)** due to N=3 sample size limitations per the Project Plan.
- **SC-006**: All scripts run end-to-end without errors on the provided data.

## 6. Data Models
- `diffusion_results`: Stores MSD slope, R², D_calc, D_scaled.
- `bootstrap_stats`: Stores mean MAE, CI_lower, CI_upper, iterations.
- `sensitivity_report`: Stores start_time_fraction, D_value, variance.

## 7. Constraints
- Compute budget: ~7 GB RAM, ~14 GB disk.
- No GPU required for MARTINI simulations of these small systems.
- All data loading must use the curated JSON file; no synthetic fallbacks.