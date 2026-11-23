# Specification: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## 1. Introduction
This project investigates the accuracy of Molecular Dynamics (MD) simulations in predicting self‑diffusion coefficients for solvents (water, ethanol, acetone) across varying timescales.

## 2. User Stories
- **US1**: As a researcher, I want to generate timescale‑accuracy curves for solvents so that I can assess convergence. (See FR-001, FR-002, FR-008)
- **US2**: As a researcher, I want to validate methodological rigor via sensitivity analysis so that I can confirm robustness. (See FR-004, FR-009)
- **US3**: As a researcher, I want to execute full batch analysis with statistical confidence intervals so that I can report on trends. (See FR-003, FR-008, SC-001, SC-003, SC-004, SC-005, SC-006)

## 3. Functional Requirements
- **FR-001**: System must load experimental diffusion coefficients from `data/raw/nist_refs.json`. (See US1)
- **FR-002**: System must extract mean‑squared‑displacement (MSD) trajectories from MD simulation output, apply the diffusive‑window fit (see FR-003), and compute the diffusion coefficient *D* from the linear regression slope. (See US1)
- **FR-003**: Define the diffusive fitting window by discarding the first **0.1** of trajectory time (ballistic regime) and fitting a linear model to the remaining data; the fit must achieve **R² ≥ 0.95**. (See US3)
- **FR-004**: System must perform bootstrap resampling of MAE estimates with **1000 iterations** on the reference hardware (multi‑core 2.5 GHz CPU). No automatic reduction of the iteration count is permitted; bootstrap runs exceeding **5.5 hours wall‑clock** must be reported and investigated as a performance issue. (See US2)
- **FR-008**: System must generate timescale‑accuracy curves (MAE vs. simulation duration) with **95 % confidence bands** for each solvent, perform descriptive trend analysis, and conduct a **paired‑bootstrap hypothesis test** to assess whether the MAE at 1 ns differs significantly from that at 10 ns (reporting the resulting p‑value). (See US1, US3)
- **FR-009**: All scripts must execute end‑to‑end without errors for the defined workflow (serves US3). (See US3)

## 4. Assumptions
- Experimental diffusion data are manually curated and stored in `data/raw/nist_refs.json` because NIST does not provide a programmatic API for this specific dataset.  
- The OPLS‑AA atomistic force field provides sufficient accuracy for the relative comparisons required by this study.  
- Reference hardware for timing benchmarks is a multi‑core CPU with a typical desktop‑class core count, operating at 2.5 GHz and ~16 GB RAM; no GPU is required for the simulated systems.

## 5. Success Criteria
- **SC-001**: Timescale‑accuracy curves (MAE vs. duration) with 95 % confidence bands are generated for all solvents at **1 ns**, **5 ns**, and **10 ns** durations. (See FR-008)
- **SC-003**: Bootstrap confidence intervals (at a conventional confidence level) are calculated for MAE estimates using the iteration policy in FR‑004. (See FR-004)
- **SC-004**: Summary tables include mean MAE, 95 % CI, and descriptive trend analysis per solvent. (See FR-008)
- **SC-005**: The paired‑bootstrap hypothesis test (as specified in the study protocol) reports a p‑value indicating whether the MAE at 1 ns differs from that at 10 ns; results are included in the final report. (See FR-008)
- **SC-006**: All scripts run end‑to‑end without errors for the defined workflow (serves US3). (See FR-009)

## 6. Data Models
- `diffusion_results`: Stores MSD slope, R², *D_calc*, *D_scaled*.  
- `bootstrap_stats`: Stores mean MAE, CI_lower, CI_upper, iterations.

## 7. Constraints
- Compute budget: on the order of a few GB of RAM and tens of GB of disk space.  
- No GPU required for OPLS‑AA simulations of these small systems.  
- All data loading must use the curated JSON file; no synthetic fallbacks.
