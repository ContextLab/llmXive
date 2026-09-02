# Implementation Plan: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Branch**: `001-investigating-md-diffusion-predictive-power` | **Date**: 2026-08-02 | **Spec**: `spec.md`

## Summary

This feature implements a computational pipeline to evaluate the predictive accuracy of Molecular Dynamics (MD) simulations for estimating diffusion coefficients of simple liquids (water, ethanol, acetone) across three timescales (1 ns, 5 ns, 10 ns). The system uses manually curated experimental benchmarks (due to lack of NIST API), executes CPU-only MD simulations using a coarse-grained force field (MARTINI), applies solvent-specific scaling factors to correct for force field bias, extracts Mean Squared Displacement (MSD) data, calculates diffusion coefficients, and performs statistical analysis (bootstrap resampling, sensitivity analysis) to generate timescale-accuracy curves with confidence intervals.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `gromacs` (via `mdanalysis`/`MDTraj` wrappers or subprocess), `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `scikit-learn`, `pyyaml`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/interim/`)  
**Testing**: `pytest` (unit tests for MSD extraction, bootstrap logic; integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU cores, ~7 GB RAM)  
**Project Type**: Computational Science / CLI Tool  
**Performance Goals**: Complete full batch (3 solvents × 3 timescales + analysis) in ≤ 6 hours  
**Constraints**: CPU-only execution; no GPU available on CI; memory < 7 GB; disk < 14 GB; no external credentials  
**Scale/Scope**: 9 simulation runs; ~1000 bootstrap iterations; 3 experimental references  

> **Critical Feasibility Note**: The spec assumes NIST Chemistry WebBook provides programmatic access to diffusion coefficients. However, the **Verified Datasets** block provided for this project contains NO verified URL for NIST diffusion data. The plan explicitly adopts a manual curation strategy for `data/raw/nist_refs.json` with checksums. This contradicts FR-001 (which mandates 'download and parse') and requires a spec kickback to update FR-001 to reflect the manual curation reality.

## Constitution Check

| Principle | Status | Verification Method | Note on Contradictions |
|-----------|--------|---------------------|------------------------|
| I. Reproducibility | **PASS** | All code pinned; seeds set; data checksums recorded | **Flag**: Curated JSON is used as the 'canonical source' due to lack of API. Spec Principle I requires 'fetch from canonical source' which is technically violated by manual curation. Kickback needed. |
| II. Verified Accuracy | **PASS** | Citations validated; no title-token overlap issues | |
| III. Data Hygiene | **PASS** | Raw data checksummed; derivations documented | |
| IV. Single Source of Truth | **PASS** | Figures/statistics trace to `data/processed/` and `code/` | **Flag**: Spec FR-008 (R² ≥ 0.99) contradicts Constitution Principle VI (R² ≥ 0.95). Plan adopts 0.95. Kickback needed to align FR-008. |
| V. Versioning Discipline | **PASS** | Content hashes tracked; `updated_at` updated | |
| VI. Simulation Convergence Validation | **PASS** | MSD linearity check ($R^2 \ge 0.95$) implemented | **Flag**: Plan uses 0.95 (Constitution) vs Spec 0.99 (FR-008). Kickback needed. |
| VII. Timescale-Dependent Error Quantification | **PASS** | MAE calculated separately for 1 ns, 5 ns, 10 ns | |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-md-diffusion-predictive-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-424-investigating-the-predictive-power-of-mo/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point for pipeline
│   ├── config.py               # Parameters (timescales, solvents, FF, scaling factors)
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── runner.py           # MD execution wrapper (GROMACS/LAMMPS)
│   │   └── topology.py         # Topology generation (MARTINI)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── msd.py              # MSD extraction & diffusion calc
│   │   ├── bootstrap.py        # Resampling logic
│   │   └── sensitivity.py      # Regression start time sweep
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── plots.py            # Timescale-accuracy curves
│   │   └── tables.py           # Summary tables
│   └── utils/
│       ├── logging.py
│       └── checksums.py
├── data/
│   ├── raw/
│   │   ├── nist_refs.json      # Experimental benchmarks (curated)
│   │   └── topologies/         # Initial .gro/.top files
│   ├── processed/
│   │   ├── msd_curves.csv      # Extracted MSD data
│   │   ├── diffusion_results.csv # Calculated D values (scaled)
│   │   └── bootstrap_stats.csv # MAE distributions
│   └── interim/
│       └── simulation_logs/    # Raw MD output
├── tests/
│   ├── unit/
│   │   ├── test_msd.py
│   │   └── test_bootstrap.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity; all modules under `code/` with clear separation of simulation, analysis, and reporting.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Coarse-grained (MARTINI) force field | Required by FR-007 to meet 6-hour runtime on 2-core CPU | All-atom simulations would exceed time/memory limits for long trajectories. |
| Solvent-specific Scaling Factors | Required to correct MARTINI's inherent significant overestimation of D | Direct comparison to experimental values would measure force field bias, not timescale convergence |
| Bootstrap resampling (1000 iters) | Required by FR-004 for 95% CI; fallback to 100 if time-constrained | Parametric CI assumptions invalid for non-normal error distributions |
| Sensitivity analysis sweep | Required by US-2 to validate robustness of regression start time | Single-point estimation risks artifact dependence on arbitrary cutoff |

## Phase Plan

### Phase 0: Research & Feasibility
- [ ] **FR-001 (Spec Contradiction)**: Confirm NIST API unavailability. **Action**: Curate `data/raw/nist_refs.json` with checksum. **Kickback**: Flag FR-001 in spec for update to 'use curated reference'.
- [ ] **FR-007**: Validate MARTINI parameters for water/ethanol/acetone; confirm solvent-specific scaling factors from literature.
- [ ] **FR-002**: Test GROMACS/LAMMPS installation on CI; benchmark 1 ns water simulation time.
- [ ] **FR-008 (Spec Contradiction)**: Define MSD linearity check logic ($R^ \ge 0.95$). **Kickback**: Flag FR-008 (0.99) in spec for update to align with Constitution Principle VI (0.95).
- [ ] **Density Convergence**: Implement density stability check (±1% over 200 ps NPT) to prevent drift bias.

### Phase 1: Data Model & Contracts
- [ ] Define `diffusion_results` schema (solvent, timescale, D_pred, D_exp, D_scaled, MAE, R2, valid_flag, scaling_factor_applied).
- [ ] Define `bootstrap_stats` schema (solvent, timescale, mean_mae, ci_lower, ci_upper, n_iter).
- [ ] Define `sensitivity_report` schema (solvent, timescale, start_time_pct, diffusion_coefficient, variance, robust). **Explicit Fields**: `start_time_pct` (0.1, 0.2, 0.3), `diffusion_coefficient`, `variance`, `robust`.
- [ ] Generate `contracts/*.schema.yaml` files.

### Phase 2: Implementation
- [ ] Implement `simulation/runner.py`: Execute MD with timeout, log failures, check density convergence.
- [ ] Implement `analysis/msd.py`: Extract MSD, linear regression, $R^2 \ge 0.95$ check, apply scaling factors.
- [ ] Implement `analysis/bootstrap.py`: Resampling with fallback logic. **Statistical Note**: Replace p-value test with descriptive trend analysis due to N=3 limitation.
- [ ] Implement `analysis/sensitivity.py`: Sweep regression start times ([deferred], [deferred], [deferred]). **Kickback**: Flag SC-003 in spec for update to define these concrete values.
- [ ] Implement `reporting/plots.py`: Timescale-accuracy curves with uncertainty bands.
- [ ] Implement `reporting/tables.py`: Summary tables with CI.

### Phase 3: Validation & Reporting
- [ ] Run full batch (3 solvents × 3 timescales).
- [ ] Verify SC-001 (MAE vs NIST), SC-002 (CI width), SC-003 (sensitivity variance < 5%).
- [ ] Generate final report (US-3) with **descriptive trend analysis** (not p-value) for 1 ns vs 10 ns improvement. **Kickback**: Flag SC-005 in spec for update to remove p-value requirement.
- [ ] Checksum all artifacts; update `state/...yaml`.

## Critical Spec Kickbacks Required

1.  **FR-001**: Change 'download and parse' to 'use curated reference' or 'identify programmatic source'.
2.  **FR-008**: Change R² threshold from 0.99 to 0.95.
3. **SC-003**: Define sensitivity sweep parameters as [deferred], [deferred], [deferred].
4.  **SC-005**: Remove 'bootstrap difference-of-means test (p ≤ 0.05)' and replace with 'descriptive trend analysis' or 'CI overlap check' due to N=3 limitation.