# Research: Testing the Equivalence Principle with Satellite Laser Ranging

## Overview

This research document outlines the data strategy, methodological approach, and computational constraints for testing the Weak Equivalence Principle (WEP) using Satellite Laser Ranging (SLR) data. The primary goal is to determine if satellites of differing composition exhibit measurable differential accelerations ($a_c$) that would imply a violation of the WEP, quantified by the Eötvös parameter ($\\eta$).

**Critical Methodology Correction**: The initial approach of subtracting independent non-gravitational acceleration estimates is **invalid**. This plan adopts a **joint estimation** strategy where $\\eta$ is a shared parameter in a single least-squares adjustment of the satellite pair. This ensures common-mode errors (e.g., geopotential) cancel, isolating the differential gravitational signal.

## Dataset Strategy

### Verified Datasets

The following datasets are verified and available for use. **Note:** The spec requests data for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette from the ILRS archive. However, the verified datasets block indicates **NO verified source found** for these specific satellites or the ILRS archive directly. The available verified SLR datasets on HuggingFace are generic or language-specific (e.g., Turkish, Catalan) and do not contain the required geodetic satellite telemetry.

| Dataset Name | Verified URL | Usage in Plan | Status |
|--------------|--------------|---------------|--------|
| SLR (Generic Parquet) | ` | **UNUSABLE** for this study. Contains generic SLR data, not specific geodetic satellite normal points. | **MISMATCH** |
| Open_SLR108 (Turkish) | ` | **UNUSABLE**. Speech recognition dataset. | **MISMATCH** |
| OpenSLR-69 (Catalan) | ` | **UNUSABLE**. Speech recognition dataset. | **MISMATCH** |
| LAGEOS-1 | NO verified source | **REQUIRED** by spec. | **BLOCKING** |
| LAGEOS-2 | NO verified source | **REQUIRED** by spec. | **BLOCKING** |
| ILRS Archive | NO verified source | **REQUIRED** by spec. | **BLOCKING** |
| Composition Metadata | NO verified source | **REQUIRED** (mass, material) for $\\eta$ calculation. | **BLOCKING** |

### Dataset-Variable Fit Analysis

**Critical Mismatch Identified:**
The study requires specific variables:
1. **Timestamp**: Time of observation.
2. **Range**: Distance measurement (meters).
3. **Satellite ID**: Must distinguish between LAGEOS-1, LAGEOS-2, etc.
4. **Station ID**: For geometric correction.
5. **Composition Metadata**: Mass, surface area, material properties (for differential acceleration calculation).

The verified datasets provided in the "# Verified datasets" block do **not** contain these variables. They are either generic SLR data without satellite differentiation or entirely unrelated speech datasets. The ILRS archive (the canonical source for LAGEOS/Etalon data) has **no verified URL** in the provided block.

**Implication:**
The plan **cannot proceed** with the current verified dataset list. The implementation will fail to download the required data.
* **Action**: The `ingestion.py` script will check the `# Verified datasets` block. If no valid source is found, it will raise a `DataUnavailableError` and exit. **No fallback to unverified URLs is permitted** per Constitution Principle II.
* **Mitigation**: The project must be paused until a verified source for LAGEOS SLR normal points and composition metadata is added to the verified dataset block.

**Decision:**
For the purpose of this plan, we assume the `ingestion.py` script will implement a strict check. If the verified block is empty, the pipeline halts. The plan proceeds with the *methodology* assuming data becomes available, but the *execution* is blocked until a verified source is provided.

## Methodology

### 1. Data Ingestion and Pre-processing (US-1)

* **Input**: SLR normal-point series (Time, Range, Satellite ID, Station ID).
* **Process**:
 1. **Verify Source**: Check if a verified URL exists in the `# Verified datasets` block. If not, raise `DataUnavailableError`.
 2. Download raw data from the source.
 3. Parse into a `NormalPoint` structure.
 4. Filter outliers: Remove points with residuals > 2 cm (based on pre-fit solution) or quality flags.
 5. Time-align: Convert timestamps to a unified epoch (e.g., TAI).
 6. **Validation**: Ensure ≥ 95% of available points are retained; check for NaNs.
* **Constraint**: Handle missing data gracefully (log warning, proceed with available satellites) **ONLY IF** the satellite has a verified source.

### 2. Differential Acceleration Parameter Estimation (US-2) - **REVISED**

* **Dynamical Model**:
 * **Geopotential**: GGM05C (primary), EGM2008, GOCO06s (for sensitivity).
 * **Non-Gravitational**: Atmospheric drag (Jacchia model), Solar Radiation Pressure (SRP) with adjustable coefficients, Earth albedo.
 * **Relativity**: General Relativistic corrections (Schwarzschild, Lense-Thirring, de Sitter).
* **Estimation Strategy (Joint Fit)**:
 * Perform a **single joint weighted least-squares fit** for the satellite pair (e.g., LAGEOS-1 & LAGEOS-2).
 * **Parameters**: Orbital elements for both satellites, non-gravitational coefficients (drag, SRP), and the **shared differential parameter** $\\eta$ (or $a_c$).
 * **Model Formulation**: The observation equation for the pair includes a term $\\eta \\cdot \\Delta g_{comp}$, where $\\Delta g_{comp}$ is the difference in gravitational acceleration predicted by the WEP violation model based on composition.
 * **Convergence**: Residuals < 1e-5 meters.
* **Calculation**:
 * The solver directly estimates $\\eta$ and its covariance $\\Sigma_{\\eta}$.
 * **Uncertainty**: Propagate covariance matrices to derive 95% CI for $\\eta$.
 * **Interpretation**: $\\eta$ represents the deviation from the common-force model. If $\\eta \\neq 0$, it indicates a WEP violation **or** a differential model error. Sensitivity analysis bounds the latter.

### 3. Statistical Validation and Robustness (US-3)

* **Model Comparison**:
 * **Null Model ($H_0$)**: $\\eta = 0$ (WEP holds).
 * **Alternative Model ($H_1$)**: $\\eta \\neq 0$ (WEP violated).
 * **Test**: Likelihood Ratio Test (LRT) or F-test comparing the $\\chi^2$ of the Null vs. Alternative joint models.
* **Sensitivity Analysis**:
 * Run estimation with 3 distinct geopotential models (GGM05C, EGM2008, GOCO06s).
 * Calculate Z-scores ($\\eta / SE_\\eta$) for each.
 * **Threshold**: If Z-score variation > 20%, flag as "Unreliable due to geopotential uncertainty".
* **Multiple Comparisons**:
 * Apply configurable corrections: **Bonferroni** (default), **Holm-Bonferroni**, or **Benjamini-Hochberg**.
 * Report adjusted p-value.

### 4. Compute Feasibility (US-4)

* **Environment**: GitHub Actions free-tier (A minimal virtual machine configuration with a low vCPU count, constrained RAM, and a 6h limit.).
* **Strategy**:
 * **Data Sampling**: If full multi-year data exceeds RAM, sample a representative subset (e.g., 1 year) for the initial run.
 * **CPU-Only**: Use `scipy.optimize.least_squares` and `numpy` for linear algebra. No GPU libraries.
 * **Parallelization**: Run sensitivity analysis (different geopotential models) in parallel threads if memory permits, or sequentially to stay within RAM limits.
 * **Timeout**: Implement a configurable hard timeout with graceful shutdown and partial result logging..

## Statistical Rigor & Assumptions

* **Causal Inference**: The study is observational. Findings regarding $\\eta$ are framed as **associational limits** or upper bounds, not causal proofs, unless a specific identification strategy is introduced.
* **Measurement Validity**: Assumes ILRS data is calibrated and valid.
* **Collinearity**: Acknowledges that non-gravitational forces (drag vs. SRP) may be correlated; covariance propagation handles this.
* **Power Analysis**: Sample size (number of normal points) is assumed sufficient for the required precision based on spec assumptions. If data is sparse (< 500 points), the satellite is excluded.
* **Benchmark Reference**: For SC-002, the plan will compare the width of the 95% CI against **Müller et al. (2010)** or **NASA MICROSCOPE** state-of-the-art benchmarks (values to be loaded from `config.py`).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No Verified Data Source** | **Critical** (Project cannot run) | Pipeline halts with `DataUnavailableError`. No fallback to unverified URLs. |
| **Geopotential Model Error** | High (False positives) | Sensitivity analysis with 3 models; flag if Z-score variation > 20%. |
| **Compute Time Exceeded** | Medium (Pipeline fails) | Sample data; optimize code; implement 5.5h timeout. |
| **Convergence Failure** | Medium (No result) | Relaxed tolerance retry; log best-fit parameters. |
| **Missing Composition Metadata** | Critical (Cannot calculate $\\eta$) | Pipeline checks for metadata; fails if missing. |
