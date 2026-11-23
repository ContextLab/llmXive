# Specification: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Project Overview
This project investigates the predictive accuracy of Molecular Dynamics (MD) simulations using the MARTINI force field for estimating diffusion coefficients of simple liquids (water, ethanol, acetone) compared to experimental NIST benchmarks.

<!-- Updated by T008a on 2023-10-27 12:00:00: Aligned FR-008 with Constitution Principle VI (R² >= 0.95) -->

## Functional Requirements

### FR-001: Simulation Execution
The system shall execute MD simulations for water, ethanol, and acetone at 298K using the MARTINI force field.

### FR-002: Timescale Variation
The system shall run simulations at three distinct timescales: 1ns, 5ns, and 10ns.

### FR-003: MSD Extraction
The system shall extract Mean Squared Displacement (MSD) trajectories from simulation outputs.

### FR-004: Diffusion Calculation
The system shall calculate diffusion coefficients from the linear region of the MSD curve.

### FR-005: Benchmark Comparison
The system shall compare calculated diffusion coefficients against curated NIST reference values.

### FR-006: Error Metrics
The system shall compute Mean Absolute Error (MAE) between simulated and experimental values.

### FR-007: Runtime Limit
The system shall complete all simulations within a 6-hour wall-clock budget per solvent.

### FR-008: Linearity Threshold
The system shall validate the linearity of the MSD curve using a coefficient of determination (R²) threshold of **R² ≥ 0.95**.
*(Note: Updated from 0.99 to 0.95 to align with Constitution Principle VI as per T008a)*

### FR-009: Sensitivity Analysis
The system shall perform sensitivity analysis on regression start times.

### FR-010: Bootstrap Resampling
The system shall perform bootstrap resampling to estimate confidence intervals for MAE.

## Scientific Constraints (SC)

### SC-001: Force Field
Only the MARTINI 2.2 or 3.0 force field shall be used for coarse-grained simulations.

### SC-002: Temperature Control
Simulations shall maintain temperature at 298.15K ± 2K using a Berendsen or Nose-Hover thermostat.

### SC-003: Pressure Control
Simulations shall maintain pressure at 1 bar using a Parrinello-Rahman or Berendsen barostat.

### SC-004: Equilibration
Density convergence must be achieved (±1% over 200ps) before production runs.

### SC-005: Statistical Method
Due to N=3 limitations (solvents), the system shall perform **descriptive trend analysis** rather than hypothesis testing.
*(Note: Updated from 'bootstrap difference-of-means test' to 'descriptive trend analysis' as per T008b)*

### SC-006: Data Integrity
All raw data must be checksummed and tracked in `data/raw/manifest.json`.

## Data Model

### Diffusion Results
- Solvent (str)
- Timescale (float, ns)
- D_simulated (float, m²/s)
- D_experimental (float, m²/s)
- MAE (float, m²/s)
- R_squared (float)
- Valid (bool)

### Sensitivity Report
- Solvent (str)
- Timescale (float, ns)
- Start_Time_Fractions (list of float)
- D_Values (list of float)
- Variance (float)
- Pass_Threshold (bool)

## Deliverables
1. `data/processed/timescale_accuracy_curves.png`: Plot of MAE vs. Simulation Duration.
2. `data/processed/summary_table.csv`: Summary of all results with confidence intervals.
3. `data/processed/sensitivity_report.json`: Sensitivity analysis results.
4. `data/processed/final_report.md`: Comprehensive analysis report.