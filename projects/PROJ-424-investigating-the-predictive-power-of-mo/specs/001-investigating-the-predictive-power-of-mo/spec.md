# Specification: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## 1. Introduction
This project investigates the accuracy of Molecular Dynamics (MD) simulations in predicting self‑diffusion coefficients for solvents (water, ethanol, acetone) across varying timescales.

## 2. User Stories
- **US1**: As a researcher, I want to generate timescale‑accuracy curves for solvents so that I can assess convergence.
- **US2**: As a researcher, I want to validate methodological rigor via sensitivity analysis so that I can confirm robustness.
- **US3**: As a researcher, I want to execute full batch analysis with statistical confidence intervals so that I can report on trends.

## 3. Functional Requirements
- **FR-001**: System must load experimental diffusion coefficients from `data/raw/nist_refs.json`.  
- **FR-002**: System must extract mean‑squared‑displacement (MSD) trajectories from MD simulation output, apply the diffusive‑window fit (see FR-003), and compute the diffusion coefficient *D* from the linear regression slope.  
- **FR-003**: Define the diffusive fitting window by discarding the first [deferred] of trajectory time (ballistic regime) and fitting a linear model to the remaining data; the fit must achieve **R² ≥ 0.95**.  
- **FR-004**: System must perform bootstrap resampling of MAE estimates with **1000 iterations** on the reference hardware (8‑core 2.5 GHz CPU). No fallback reduction is permitted; runs exceeding **5.5 hours wall‑clock** must be reported and investigated as a performance issue.  
- **FR-005**: System must recompute diffusion coefficients across start‑time fractions **0.1**, **0.2**, **0.3** of the total trajectory, calculate the **coefficient of variation (CV = std/mean)** of the resulting *D* values, and store the results in the `sensitivity_report` data model.  
- **FR-006**: System must run MD simulations for each solvent at three durations **1 ns**, **5 ns**, **10 ns** using the **OPLS‑AA atomistic force field**; if a simulation exceeds **12 hours wall‑clock**, reduce the system size by [deferred] while remaining atomistic.
- **FR-007**: If a coarse‑grained force field is ever used, apply a literature‑based time‑scaling correction to diffusion coefficients and document the scaling factor. (Primary workflow uses OPLS‑AA; this FR supports optional alternatives.)  
- **FR-008**: System must generate timescale‑accuracy curves (MAE vs. simulation duration) with **95 % confidence bands** for each solvent, perform descriptive trend analysis, and conduct a CI‑overlap check between the 1 ns and 10 ns intervals.  
- **FR-009**: All scripts must execute end‑to‑end without errors for the defined workflow (serves US3).  
- **FR-010**: System must store results in the data models `diffusion_results`, `bootstrap_stats`, and `sensitivity_report` as specified in Section 6.

## 4. Assumptions
- Experimental diffusion data are manually curated and stored in `data/raw/nist_refs.json` because NIST does not provide a programmatic API for this specific dataset.  
- The OPLS‑AA atomistic force field provides sufficient accuracy for the relative comparisons required by this study.  
- Reference hardware for timing benchmarks is a multi‑core CPU with a typical desktop‑class core count, operating at 2.5 GHz and ~16 GB RAM.; no GPU is required for the simulated systems.

## 5. Success Criteria
- **SC-001**: Timescale‑accuracy curves (MAE vs. duration) with 95 % confidence bands are generated for all solvents at **1 ns**, **5 ns**, and **10 ns** durations.  
- **SC-002**: Sensitivity analysis shows the **coefficient of variation (CV) of D across start‑time fractions 0.1, 0.2, 0.3 is < 5 %** for each solvent.  
- **SC-003**: Bootstrap confidence intervals (95 %) are calculated for MAE estimates using the iteration policy in FR‑004.  
- **SC-004**: Summary tables include mean MAE, 95 % CI, and descriptive trend analysis per solvent.  
- **SC-005**: Descriptive trend analysis of MAE versus simulation duration is performed, and a confidence‑interval overlap check between the 1 ns and 10 ns intervals is reported.  
- **SC-006**: All scripts run end‑to‑end without errors for the defined workflow (serves US3).

## 6. Data Models
- `diffusion_results`: Stores MSD slope, R², *D_calc*, *D_scaled*.  
- `bootstrap_stats`: Stores mean MAE, CI_lower, CI_upper, iterations.  
- `sensitivity_report`: Stores start_time_fraction, D_value, CV, variance.

## 7. Constraints
- Compute budget: ~7 GB RAM, ~14 GB disk.  
- No GPU required for OPLS‑AA simulations of these small systems.  
- All data loading must use the curated JSON file; no synthetic fallbacks.

