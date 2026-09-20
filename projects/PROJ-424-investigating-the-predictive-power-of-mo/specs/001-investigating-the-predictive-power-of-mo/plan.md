# Implementation Plan: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Branch**: `001-investigating-md-diffusion-predictive-power` | **Date**: 2026-08-02 | **Spec**: `specs/001-investigating-md-diffusion-predictive-power/spec.md`
**Input**: Feature specification from `/specs/001-investigating-md-diffusion-predictive-power/spec.md`

## Summary
This project validates the accuracy of Molecular Dynamics (MD) simulations using the MARTINI force field in predicting self-diffusion coefficients for water, ethanol, and acetone. The plan addresses the convergence panel's rejection of hardcoded/fabricated results by mandating a real, reproducible simulation pipeline using `gromacs` (via `mdtraj`/`mdanalysis` wrappers) and statistical bootstrapping against manually curated experimental benchmarks. The study generates timescale-accuracy curves (MAE vs. Duration) and performs sensitivity analysis without fabricating p-values, adhering to the N=5 sample size constraint (with fallback to N=3) and the descriptive trend analysis requirement.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `gromacs` (system binary, assumed available or containerized), `mdtraj`, `mdanalysis`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`). No external database.  
**Testing**: `pytest` (unit tests for data loading, schema validation, statistical calculations).  
**Target Platform**: Linux (GitHub Actions Runner / Local Ubuntu).  
**Project Type**: Computational Science / Simulation Pipeline.  
**Performance Goals**: Complete batch analysis (1ns, 5ns, 10ns) for 3 solvents within 6 hours CPU time.  
**Constraints**: ~7 GB RAM, ~14 GB disk. No GPU required for MARTINI of small systems (100-500 molecules).  
**Scale/Scope**: 3 solvents × 3 durations × 5 seeds = 45 simulation trajectories (Target). Fallback: 3 seeds (27 trajectories) if time > 5.5h.

> **Critical Note on Data**: The plan relies on `data/raw/nist_refs.json` (manually curated) for ground truth. Simulation trajectories must be generated using `gromacs` or loaded from `data/raw/simulations/` if pre-generated to ensure reproducibility. The "Fabricated Result" concern is resolved by ensuring the pipeline executes the actual physics simulation or loads real trajectory files, never generating synthetic numbers.

## Constitution Check

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|----------------------|
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/simulations/run_simulation.py`. All data loading from `data/`. |
| **II. Verified Accuracy** | **Pass** | Experimental values in `nist_refs.json` are manually curated from primary NIST sources (no API). |
| **III. Data Hygiene** | **Pass** | `data/raw/nist_refs.json` checksummed. Simulation outputs written to `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **Pass** | All figures/tables generated programmatically from `data/processed/diffusion_results.csv`. |
| **V. Versioning** | **Pass** | Artifact hashes tracked in `state/`. |
| **VI. Simulation Convergence** | **Pass** | `code/analysis/validate_convergence.py` enforces $R^2 \ge 0.95$ on MSD linear fit (lag-time > 100ps) before extracting $D$. |
| **VII. Timescale-Dependent Error** | **Pass** | Analysis stratified by duration (1, 5, 10 ns) to generate MAE vs. Duration curves. |

## Project Structure

### Documentation (this feature)
```text
specs/001-investigating-md-diffusion-predictive-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
projects/PROJ-424-investigating-the-predictive-power-of-mo/
├── code/
│   ├── __init__.py
│   ├── simulations/
│   │   ├── __init__.py
│   │   ├── run_simulation.py       # GROMACS wrapper, seed handling, N=5 loop
│   │   └── topology_builder.py     # MARTINI topology generation
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── msd_calculator.py       # MSD vs Time, R2 check (lag-time > 100ps)
│   │   ├── diffusion_estimator.py  # Slope extraction, scaling
│   │   └── bootstrap_analyzer.py   # Resampling, CI calculation
│   ├── data/
│   │   ├── __init__.py
│   │   └── loader.py               # JSON loader, validation
│   └── utils/
│       └── logger.py
├── data/
│   ├── raw/
│   │   ├── nist_refs.json          # Curated experimental values
│   │   └── simulations/            # (Optional) Pre-generated .xtc/.gro
│   └── processed/
│       ├── diffusion_results.csv
│       └── sensitivity_report.json
├── tests/
│   ├── test_msd.py
│   └── test_loader.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular `code/` subdirectories for simulations, analysis, and data. This minimizes overhead for a computational study and aligns with the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Real Simulation Pipeline (N=5)** | Required to resolve "FABRICATED-RESULT" concern and provide variance estimation (N>1). | Using hardcoded values or synthetic data is explicitly forbidden by the project constitution and the rejection criteria. N=1 is insufficient for variance. |
| **Bootstrap with Fallback** | FR-004 requires 1000 iterations but mandates a fallback to 100 if time > 5.5h. | A fixed 1000 iteration count without a fallback risks CI timeout on the free-tier runner. |
| **R² Gate (Lag-Time)** | Constitution Principle VI requires strong validation on the diffusive regime only. | Skipping the lag-time exclusion risks calculating D from non-diffusive (ballistic) motion. |
| **Time Budget Adjustment** | Realistic overhead (15 min/run) exceeds 6h for 45 runs. | The plan implements a "Balanced Fallback" to N=3 seeds (27 runs) if time > 5.5h to ensure the CI budget is respected while maintaining a balanced design. |

## Time Budget & Feasibility

**Target**: 45 runs (3 solvents × 3 durations × 5 seeds).
**Estimated Cost per Run**: [deferred] (100ps equilibration + 1-10ns production + topology generation).
**Total Target Time**: 45 × 15 min = 11.25 hours (Exceeds 6h CI limit).

**Mitigation Strategy**:
1.  **Streaming/Chunked Execution**: Runs are processed in batches of 5. Analysis and disk cleanup occur between batches to free memory.
2.  **Balanced Fallback**: If the cumulative wall-clock time exceeds 5.5 hours, the pipeline automatically reduces the number of seeds from 5 to 3 per condition (Total N=27). This ensures a balanced design (equal N for all conditions) while respecting the 6-hour limit.
3.  **Optimization**: Use `mdrun -nt` with a thread count matching the available cores to maximize CPU utilization on the runner.

**Feasibility Confirmation**: With the fallback to N=3, the total time is 27 × 15 min = 6.75 hours. This is still tight. The plan assumes that 10ns runs are the bottleneck. If 10ns runs are skipped in the fallback (reducing N=3 to N=2 for 10ns only), the time is reduced. However, the primary fallback is to N=3 seeds for all durations. If this still exceeds 6h, the CI job will fail, and the "Balanced Fallback" logic in `run_simulation.py` will be triggered to reduce further to N=2 if necessary. The plan explicitly acknowledges this risk and prioritizes data integrity over completing all 45 runs if time is insufficient.

**Note**: The "15-minute" estimate includes the overhead of topology generation and equilibration, addressing the concern that setup alone takes 15-30 minutes. The plan is designed to be realistic about these costs.

## Statistical Rigor & Methodological Notes

- **Sample Size**: N=5 seeds per condition (Target) or N=3 (Fallback). This provides df=4 or df=2 for variance estimation, sufficient for bootstrap resampling of the error distribution.
- **Lag-Time Analysis**: The first 100ps of every trajectory is discarded to avoid the ballistic regime. The linear fit is performed only on t > 100ps.
- **Scaling Factors**: Fixed constants from literature (Water: 0.6, Ethanol: 0.7, Acetone: 0.7). Not fitted.
- **CI Overlap**: Descriptive only. No p-values.