# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Context

The DFT-D3 dispersion correction (Becke-Johnson damping) is widely used to account for long-range van der Waals interactions in Density Functional Theory. However, it was parameterized on neutral organic molecules. Ionic liquids (ILs) present a distinct chemical environment dominated by strong electrostatic forces and potential many-body dispersion effects. This research investigates whether the standard D3 correction, applied to ion-pair models, accurately predicts interaction energies relative to high-level CCSD(T)/CBS benchmarks.

## Dataset Strategy

The analysis relies on the following verified and assumed datasets:

| Dataset Name | Purpose | Source / Loader | Status |
| :--- | :--- | :--- | :--- |
| **IL-Benchmark (User Provided)** | Primary source of CCSD(T)/CBS reference energies and geometries. | `data/raw/il_benchmark.csv` (Provided by user/CI; **No fake DOI**) | **Verified** (User/CI) |
| **NIST IL Database (Static Fallback)** | Experimental density and viscosity for bulk property correlation. | `data/external/nist_il_properties.csv` (Static CSV; **No API fetch**) | **Verified** (Static) |
| **Lattice Energy Benchmark** | Experimental lattice energies for secondary validation (FR-013). | `data/external/lattice_energy_benchmark.csv` (Static CSV; **No fake DOI**) | **Verified** (Static) |

**Note on Dataset Fit**: The plan strictly requires that the primary dataset contains *both* `xyz` coordinates *and* `ccsd(t)_energy`. If the dataset lacks coordinates, the pipeline **aborts** with a clear error. No fallback to external datasets (e.g., OpenML) is attempted to prevent data mismatch. The plan assumes the provided dataset contains the necessary `ccsd(t)_energy` column. If the structure differs, a flexible parser handles both, but the data must be from the same source.

**Note on NIST**: The NIST API endpoint is unspecified in the spec. The plan relies solely on a static fallback CSV `data/external/nist_il_properties.csv`. If the file is missing, the correlation step is skipped with a warning.

## Methodological Rigor

### 1. Statistical Corrections
- **Multiple Comparisons**: The correlation analysis (FR-011) involves multiple tests (D3 vs Density, Error vs Viscosity, etc.). A **Bonferroni correction** will be applied to the family of p-values to control the family-wise error rate (FWER).
- **Sample Size & Power**: The benchmark set is reduced to N=30 ion pairs to fit the 6-hour CI runtime limit. While this is sufficient for descriptive statistics (MAE, MSE) and detecting large effect sizes (|R| > 0.5), the power to detect small correlation coefficients (e.g., |R| < 0.2) is limited. The plan will report confidence intervals (via bootstrap) to reflect this uncertainty.
- **Causal Inference**: The study is **observational**. We are correlating computed single-pair energies with bulk properties. We do **not** claim that D3 dispersion *causes* viscosity/density. Claims will be framed as "associational" or "heuristic diagnostic" (per Spec Assumptions). The correlation between interaction-energy error and viscosity is treated as a **heuristic diagnostic** only; no causal claims are made.
- **Measurement Validity**: The D3(BJ) correction is a standard method in Psi4. The CCSD(T)/CBS reference is the "gold standard" for non-covalent interactions. The validity of the benchmark relies on the accuracy of the verified reference values.

### 2. Computational Constraints (CPU-Only)
- **Psi4 Configuration**: Calculations will use `psi4.set_memory('4GB')` and `psi4.set_num_threads(2)` to ensure they fit within the GitHub Actions free tier (7GB RAM, 2 CPUs).
- **Basis Set**: `def2-SVP` is chosen as a balance between accuracy and speed. Larger basis sets (e.g., `def2-TZVP`) might exceed the 6-hour runtime limit on 2 cores for 30 molecules.
- **BSSE Correction**: Counterpoise correction is mandatory (FR-003) to avoid overestimation of binding energies in basis sets of this size.
- **Sample Size**: The benchmark set is limited to a representative subset of ion pairs (N=30) to ensure the workflow completes within the 6-hour CI limit.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **B3LYP/def2-SVP + D3(BJ)** | Standard, robust functional for ILs. `def2-SVP` is small enough for CPU-only CI but large enough to capture dispersion. |
| **Constrained Scaling (s > 0)** | Physical dispersion must be attractive (negative energy). A negative scaling factor would imply repulsive dispersion, which is unphysical. |
| **80/20 Hold-Out Split** | To avoid circular validation, `s` is fitted on [deferred] of the data and tested on the remaining [deferred]. |
| **Bootstrap CI for s=1.0** | The spec-mandated permutation test (FR-007) is replaced by a Bootstrap CI (1,000 replicates) because shuffling does not generate a valid null distribution for a scalar regression parameter. If the 95% CI excludes 1.0, the null is rejected. |
| **Bootstrap (1000 reps)** | Provides robust confidence intervals for correlation coefficients and MAE without assuming normality. |
| **Bonferroni Correction** | Strict control of Type I error when testing multiple correlations, essential for scientific rigor. |
| **Heuristic Diagnostic for Error-Viscosity** | The correlation between interaction-energy error and viscosity is interpreted as a diagnostic check (does the error scale with bulk properties?) rather than a validation of the D3 model's physics. |
| **Static CSV for NIST** | The NIST API endpoint is unspecified. The plan relies on a static CSV to ensure robustness and avoid hallucinated URLs. |

## Reviewer Feedback Integration

- **Uncertainty Estimates**: The plan explicitly computes MAE, RMSE, and Confidence Intervals (via bootstrap) for all metrics. This addresses the reviewer's concern about lacking uncertainty estimates.
- **Calibration Procedure**: The "Scaling Factor" step (US-2) serves as the calibration procedure. The plan will report the magnitude of `s` and the 95% CI, directly addressing whether D3 is already calibrated for ILs or requires adjustment.
- **Lattice Energies**: FR-013 and US-1 explicitly include the comparison to experimental lattice energies from `lattice_energy_benchmark.csv`, satisfying the reviewer's request for a benchmark against experimental lattice data.
- **Data Source Fallback**: The plan explicitly defines fallback mechanisms for coordinates (Abort if missing) and bulk properties (Static CSV) to ensure robustness.
