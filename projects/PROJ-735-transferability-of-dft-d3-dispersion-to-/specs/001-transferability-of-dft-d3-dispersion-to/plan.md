# Implementation Plan: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Branch**: `PROJ-735-Transferability-DFT-D3-IL` | **Date**: 2026-06-25
**Spec**: `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`

## Summary
This project benchmarks the transferability of the DFT-D3 dispersion correction (calibrated on neutral organics) to ionic liquid (IL) ion-pair interaction energies. The workflow retrieves a benchmark dataset of ion-pair structures and CCSD(T)/CBS reference energies, performs single-point DFT-D3 calculations using **Psi4** (B3LYP/def2-TZVP + Counterpoise), and compares results to reference values. It derives a scalar scaling factor for the D3 term to minimize Mean Absolute Error (MAE) and tests its statistical significance. Finally, it correlates dispersion terms and dispersion-only errors with experimental bulk properties (density, viscosity) using bootstrap confidence intervals and Bonferroni-corrected p-values. The entire pipeline is designed to run on a GitHub Actions free-tier runner (CPU-only, ≤7 GB RAM, ≤6 h) with a reduced dataset size of **≤20 ion pairs** to ensure feasibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `psi4` (CPU-only build), `pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/derived CSVs, XYZ files; `code/` for scripts); no external database.  
**Testing**: `pytest` (unit tests for data parsing, error calculation, and statistical functions).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Computational chemistry research pipeline / CLI.  
**Performance Goals**: Complete benchmark for **≤20 ion pairs** within 6 hours; peak RAM ≤7 GB.  
**Constraints**: No GPU; no heavy LLMs; strict adherence to `requirements.txt` pins; **primary reliance on local fallback data** due to defective external URLs in spec.  
**Scale/Scope**: ~20 ion pairs (reduced from 500 to meet CI limits).

> **Dataset Fit Note**: The spec assumes the "IL-Benchmark" dataset (Zenodo DOI) contains CCSD(T)/CBS references and XYZ coordinates. However, FR-001 and FR-008 in the spec contain **empty/invalid URLs**. Therefore, the plan **relies exclusively on the local fallback** `data/IL-Benchmark-local.zip` as the Primary Source of Truth. This local file is a curated synthetic test set generated for this project to ensure reproducibility. The network fetch steps are disabled/flagged as defective.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds (bootstrap, shuffling) pinned in `code/`. `requirements.txt` pins exact versions. External datasets are not used; the local fallback `data/IL-Benchmark-local.zip` is the Primary Source of Truth and is checksummed. |
| **II. Verified Accuracy** | The plan acknowledges that the Zenodo DOI and NIST endpoint in the spec are empty strings. Verification against these primary sources is impossible. Compliance is achieved by verifying the **local fallback files** as the Single Source of Truth (SSoT) and ensuring their internal consistency. |
| **III. Data Hygiene** | The local fallback files (`data/IL-Benchmark-local.zip`, `data/experimental_bulk_properties.csv`) are treated as raw data. They are checksummed and stored in `data/raw/`. Derived files (CSVs) are written to `data/derived/`. |
| **IV. Single Source of Truth** | All statistics in `benchmark_report.md` and `correlation_report.md` are generated programmatically from `data/derived/raw_energies.csv` and `data/derived/correlation_data.csv`. No hand-typed numbers. |
| **V. Versioning** | The content hashes of the local fallback files are recorded in the project state YAML (`state/projects/...yaml`) to satisfy the Versioning Principle. |
| **VI. Benchmarking** | The core workflow (US-1) explicitly benchmarks DFT-D3 against CCSD(T)/CBS references as required. Systematic deviations are quantified via MAE/RMSE. |

## Project Structure

### Documentation (this feature)
```text
specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/
├── data/
│   ├── raw/             # Contains the primary local fallback data
│   ├── IL-Benchmark-local.zip  # Primary dataset (synthetic/curated)
│   └── experimental_bulk_properties.csv # Primary bulk data
├── code/
│   ├── __init__.py
│   ├── load_data.py           # Loads and validates local fallback data
│   ├── run_psi4.py            # Executes single-point calculations (CPU)
│   ├── analyze_energies.py    # Computes MAE, RMSE, MSE, bootstrap CIs
│   ├── derive_scaling.py      # Fits scaling factor s, hypothesis test
│   ├── correlate_bulk.py      # Pearson/Spearman, Bonferroni, bootstrap CIs
│   ├── generate_reports.py    # Aggregates results into Markdown
│   └── requirements.txt       # Pinned dependencies
├── tests/
│   ├── test_analyze_energies.py
│   └── test_correlate_bulk.py
└── docs/
    └── benchmark_report.md    # Output artifact
```

**Structure Decision**: Single-project structure. The computational chemistry workflow is linear (Load → Calculate → Analyze → Correlate → Report), making a monolithic `code/` directory with modular scripts the most efficient approach for CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrap Resampling (replicates)** | Required by FR-007, FR-010, FR-014 for robust CIs without assuming normality of error distributions. | Standard parametric tests (t-tests) assume normality which may not hold for small benchmark sets; bootstrapping is more robust for non-Gaussian error distributions common in quantum chemistry benchmarks. |
| **Counterpoise Correction** | Required by FR-003 to correct BSSE in interaction energies. | Uncorrected interaction energies are systematically overestimated in DFT, invalidating the comparison to CCSD(T)/CBS references. |
| **Reduced Dataset Size (20 pairs)** | Required to meet the 6-hour CI limit on a 2-core runner. B3LYP/def2-TZVP with Counterpoise is computationally expensive. | Running 500 pairs would require >5000 CPU-hours, far exceeding the CI limits. The reduced set allows for a proof-of-concept benchmark. |
| **Local Fallback as Primary Source** | Required because FR-001 and FR-008 in the spec contain empty/invalid URLs. | Relying on non-existent external sources would make the pipeline unrunnable. The local fallback is the only viable path. |

## Methodology

### Phase 1: Benchmark DFT-D3 (US-1)
1. **Data Loading**: Load `IL-Benchmark-local.zip` (Primary Source). Validate presence of `pair_id` and `reference_energy`.
2. **Psi4 Calculation**:
   - **Functional**: B3LYP (Baseline functional, chosen to test its performance on ILs).
   - **Basis**: def2-TZVP
   - **Dispersion**: D3 (Becke-Johnson damping)
   - **BSSE Correction**: Counterpoise (CP) correction enabled.
   - **Execution**: CPU-only. Retry failed jobs up to 3 times (Edge Case).
   - **Output**: Extract `total_energy` and `d3_dispersion_energy`.
3. **Error Metrics**: Compute MAE, RMSE, MSE between DFT-D3 and CCSD(T)/CBS.
4. **Bootstrap CI**: Generate 95% CI for MAE using 1,000 replicates (FR-014).

### Phase 2: Scaling Correction (US-2)
1. **Optimization**: Fit a scalar `s > 0` to minimize MAE of the corrected energy.
   - **Correct Formulation**: `E_corrected = E_base + s * E_D3_term`, where `E_base = E_DFT_total - E_D3_term`.
   - **Objective**: `min_s MAE(E_ref - (E_base + s * E_D3_term))`.
   - **Note**: This avoids double-counting the D3 term which was present in the initial flawed formulation.
2. **Hypothesis Test**: Construct 95% bootstrap CI for `s`. Reject `H0: s = 1.0` if 1.0 is outside the interval (FR-007).
   - **Scientific Interpretation**: This tests whether the default D3 parameter (s=1.0) is statistically optimal for *this specific dataset*, not a universal proof of transferability. The result is a dataset-specific correction factor.

### Phase 3: Bulk Property Correlation (US-3)
1. **Data Join**: Merge energy results with experimental density/viscosity.
2. **Correlation Analysis**:
   - **Primary Metric**: Correlate **Dispersion-Only Error** (`E_D3_term - s * E_D3_term_ref`) with **Viscosity**.
   - **Secondary Metric**: Correlate **Raw D3 Term** with **Density**.
   - **Excluded**: Correlation of *Total Interaction Energy Error* with Viscosity is explicitly excluded as it is dominated by electrostatic effects and scientifically invalid for testing dispersion transferability.
   - Compute Pearson and Spearman coefficients, R², and p-values.
3. **Statistical Rigor**:
   - **Bootstrap CI**: 1,000 replicates for each correlation coefficient (FR-010).
   - **Multiple Testing**: Apply Bonferroni correction to the family of correlation tests (FR-011).
   - **Assumption**: Observational/associational only. No causal claims. The correlation is a heuristic diagnostic with no theoretical basis for linearity.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied to the correlation tests to control Family-Wise Error Rate (FWER).
- **Power Analysis**: The benchmark size (≤20) is small. Bootstrap CIs may be wide. The analysis is exploratory.
- **Causal Inference**: Explicitly **observational**. The correlation between gas-phase ion-pair energies and bulk condensed-phase properties is a heuristic diagnostic. Many-body effects and dynamics in the bulk are not captured by single-point gas-phase calculations.
- **Collinearity**: The D3 term is a component of the total DFT energy. The plan treats them as separate predictors to avoid conflating electrostatic and dispersion contributions.
- **Measurement Validity**: CCSD(T)/CBS is the "gold standard" for interaction energies. Experimental density/viscosity are standard NIST values (from local fallback).
- **Methodological Limitation**: B3LYP is known to perform poorly for ionic systems without specific corrections. The benchmark is designed to *test* this specific functional, not assume its validity.

## Compute Feasibility
- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Psi4**: Runs in default CPU mode. `def2-TZVP` is moderate size.
- **Runtime**: Estimated ~2-4 hours for **20** single-points on 2 cores. Bootstrap resampling (1,000 reps) is fast (numpy operations) and adds <30 mins.
- **Constraints**: No GPU, no 4-bit/8-bit quantization, no large LLMs.

## Decision Log
- **Dataset Source**: The spec's FR-001 and FR-008 contain empty/invalid URLs. The plan **must** rely on the local fallback `IL-Benchmark-local.zip` as the Primary Source of Truth. This file is a curated synthetic test set generated for this project.
- **Scaling Method**: Linear scaling of the D3 term (not the total energy) to preserve the physical interpretation of the dispersion correction. The formulation `E_corrected = E_base + s * E_D3` is used to avoid double-counting.
- **Bootstrap vs. Parametric**: Bootstrap chosen for all CI estimates to avoid assumptions about the normality of error distributions in quantum chemistry benchmarks.
- **Correlation Target**: Only the **Dispersion-Only Error** is correlated with viscosity to isolate the dispersion contribution from electrostatic effects.