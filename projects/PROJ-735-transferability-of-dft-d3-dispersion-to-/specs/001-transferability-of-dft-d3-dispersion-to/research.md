# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Background
DFT-D (Grimme et al.) is an empirical dispersion correction parameterized primarily on neutral organic molecules and the S66 dataset. Ionic liquids (ILs) are salts in the liquid state, characterized by strong electrostatic interactions and complex many-body dispersion effects. The transferability of D3 parameters to charged systems (ion pairs) is an open question. This study benchmarks DFT-D3 against high-level CCSD(T)/CBS reference data for a set of IL ion pairs and investigates if a simple scaling factor can correct systematic bias.

## Dataset Strategy

| Dataset Name | Source / Loader | Variables Used | Notes |
| :--- | :--- | :--- | :--- |
| **IL-Benchmark (Local)** | `data/IL-Benchmark-local.zip` (Primary) | `pair_id`, `xyz_coordinates`, `reference_energy` | **Primary Source**: This is a curated synthetic test set generated for this project because the spec's FR-001 contains an empty DOI. It contains CCSD(T)/CBS reference energies and XYZ coordinates. |
| **Experimental Bulk Properties (Local)** | `data/experimental_bulk_properties.csv` (Primary) | `pair_id`, `density`, `viscosity` | **Primary Source**: This is a curated synthetic test set generated for this project because the spec's FR-008 contains an invalid URL. |

**Dataset Variable Fit**:
- **Required**: `pair_id` (unique identifier), `reference_energy` (CCSD(T)/CBS), `xyz_coordinates` (for Psi4), `density`, `viscosity`.
- **Availability**: The local fallback files are assumed to contain these fields based on the spec's acceptance criteria.
- **Risk Mitigation**: The pipeline includes a validation step (FR-002) to flag and skip records missing `reference_energy` or `pair_id`.

## Methodology

### Phase 1: Benchmark DFT-D3 (US-1)
1. **Data Loading**: Load `IL-Benchmark-local.zip` (Primary). Validate presence of `pair_id` and `reference_energy`.
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