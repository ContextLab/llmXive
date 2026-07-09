# Research: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

## 1. Problem Statement & Motivation

Texture evolution in FCC metals during cold rolling is a critical determinant of mechanical properties (anisotropy, formability). While the qualitative trends (e.g., evolution from Cube to Brass/Copper/S components) are well-documented, a quantitative predictive model linking **cold-rolling reduction percentage** directly to **texture descriptors** (Volume Fractions of Brass, Copper, S, Goss; Texture Index) is needed for rapid process design.

**Reviewer Feedback Integration**:
Per reviewer *rosalind-franklin-simulated*, relying solely on reduction percentage risks obscuring crystallographic mechanisms (e.g., dislocation density, stacking fault energy). This research explicitly:
1. Treats "Material Type" (Al, Cu, Ni) as a proxy for Stacking Fault Energy (SFE) but acknowledges the continuous nature of SFE.
2. Quantifies the **residual variance** attributed to unobserved microstructural variables using **Shapley value regression** or **hierarchical modeling** concepts, framing the result as an upper bound estimate of unobserved confounders (FR-008).
3. Frames all findings as **associational**, avoiding causal claims unless randomization is present (which is not the case here, per FR-006).
4. Implements a **Hold-out Physics Check** to ensure the model learns underlying physical trends rather than merely memorizing the synthetic data generator's function.

## 2. Dataset Strategy

The project relies on the following verified datasets or generation scripts. No other URLs are cited.

| Dataset Name | Description | Source URL / Generation | Usage |
|:--- |:--- |:--- |:--- |
| **ebsd-synthetic (Verified)** | Synthetic EBSD data for FCC metals. Contains orientation data and metadata. | ` (if verified to contain reduction metadata) OR **Local Generation Script** (see below) | Primary input for `data/download.py`. Used to extract orientations, confidence indices, and reduction metadata. |
| **Local Generation Script** | Python script to generate synthetic EBSD data with explicit 'reduction percentage' and 'texture evolution' parameters. | `code/data/generate_synthetic.py` (Pinned seed: 42) | Used if the HuggingFace dataset lacks specific 'reduction' metadata. Ensures the 'reduction' variable exists and is linked to texture evolution. |

**Dataset Fit & Limitations**:
- **Variable Fit**: The `ebsd-synthetic` dataset (or generated data) contains orientation data and reduction metadata. It does **not** contain direct measurements of dislocation density or grain size.
- **Mitigation**: As per FR-008, the model will explicitly calculate the portion of variance unexplained by "Material" and "Reduction" using **Shapley value regression** and report it as the "unobserved confounder" contribution. This addresses the reviewer's concern about "statistical correlation vs. physical structure" by quantifying the gap.
- **Missing Data**: If specific reduction levels (e.g., [deferred] for Ni) are missing in the source, the pipeline logs a warning (US-1, AC-3) and proceeds with interpolation or exclusion, rather than halting.
- **MTData Fallback**: The 'MTData' dataset is **not** used as a fallback for EBSD orientation data due to modality mismatch (tabular properties vs. crystallographic orientations). Missing data points are handled via interpolation or exclusion.

**Generation Parameters (if local generation is used)**:
- **Metals**: Al, Cu, Ni.
- **Reduction Levels**: [deferred], [deferred], [deferred], [deferred], [deferred].
- **Texture Evolution Model**: Based on standard FCC rolling texture evolution (e.g., Brass component increases with reduction).
- **Noise**: Added Gaussian noise to orientations to simulate experimental error.
- **Seed**: 42 (for reproducibility).

## 3. Methodology

### 3.1 Data Acquisition & Pre-processing (FR-001, FR-002)
1. **Download/Generate**: Fetch `data_synth_ebsd.zip` from the verified HuggingFace URL or run `generate_synthetic.py` with pinned seed 42.
2. **Filter**: Parse EBSD points; discard any with `confidence_index < 0.1`.
3. **Re-index**: Use `orix` to re-index all orientations to **FCC symmetry** (Point Group `m-3m`). This ensures consistency across Al, Cu, and Ni (Constitution Principle VII).
4. **Validation**: Log warnings if >50% of points are filtered for a sample (Edge Case 3).

### 3.2 Texture Quantification (FR-003)
1. **Algorithm**: Implement MTEX-style search algorithm using `orix` to identify volume fractions of:
 - Brass (B)
 - Copper (C)
 - S
 - Goss
 - Cube (optional, if data permits)
 - Random
2. **Texture Index**: Calculate the Texture Index (J-index) as a measure of overall texture strength.
3. **Mass Balance**: Verify that $\sum (\text{Volume Fractions}) = 1.0 \pm 0.01$ (US-2, AC-2).
4. **Benchmarking**: Compare calculated values against known trends (e.g., Rosenstock et al., 2018) where available, noting that exact numerical benchmarks may be limited by the synthetic nature of the data.

### 3.3 Predictive Modeling (FR-004, FR-005)
1. **Features**: `Material_Type` (Categorical: Al, Cu, Ni), `Reduction_Percentage` (Continuous: 0-80%).
2. **Models**:
 - **Polynomial Regression**: Degree 2-3 to capture non-linearity.
 - **Gaussian Process (GP)**: With a radial basis function (RBF) kernel to provide uncertainty estimates. The GP kernel is designed to capture distinct regimes for each metal (addressing the continuous SFE concern).
3. **Validation**: 5-fold Cross-Validation.
 - **Metric**: R² ≥ 0.85 (SC-003) and RMSE.
 - **Interaction Test**: Explicitly test for interaction effects between 'Material Type' and 'Reduction Percentage' using an ANOVA-based F-test on the model residuals. If significant, the model captures metal-specific evolution curves.
 - **Per-Metal Baseline**: Train separate models for each metal to compare against the joint model.
 - **Constraint**: Must run on CPU only (no GPU).
4. **Associational Framing**: All outputs explicitly state "association between reduction and texture" (FR-006).
5. **Hold-out Physics Check**: Validate that the model reproduces known qualitative trends (e.g., increasing Brass with higher reduction) for a held-out subset of the data that was not used in training, ensuring the model learns physics, not just generator noise.

### 3.4 Robustness & Sensitivity (FR-007, FR-008, FR-009)
1. **Sensitivity Analysis**: Sweep `interpolation_tolerance` over {0.01, 0.05, 0.1}.
 - **Stability Criterion**: R² variation ≤ 0.02 (SC-004).
2. **Residual Variance Decomposition**:
 - Calculate total unexplained variance ($1 - R^2$).
 - Use **Shapley value regression** or **hierarchical modeling** to partition this variance between 'Material Type' (SFE proxy) and the residual (unobserved confounders).
 - **Interpretation**: Report the residual portion as an **upper bound estimate** of the contribution of missing microstructural variables (grain size, SFE variations within metal type), explicitly stating that this is not a direct measurement but a statistical bound.
3. **Extrapolation**: Flag predictions outside the 0-80% range; apply confidence penalty factor of 2.0 (FR-009).

### 3.5 Power Analysis
- **Objective**: Determine the minimum sample size required to detect an R² of 0.85 with [deferred] power.
- **Method**: Calculate based on the expected effect size (texture evolution trend) and noise level in the synthetic data.
- **Mitigation**: If the synthetic dataset has N < 30 per metal/reduction bin, the plan will use **bootstrap resampling** to estimate the stability of the R² metric and report the confidence interval of the R² value, acknowledging the potential instability.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since multiple texture descriptors are tested, the analysis will report family-wise error rates or adjust p-values if hypothesis testing is performed (though primary focus is R²).
- **Collinearity**: "Material Type" and "Reduction" are not definitionally collinear, but "Reduction" is the sole continuous predictor. The model acknowledges that "Reduction" is a proxy for accumulated plastic strain.
- **Power Limitation**: The dataset is synthetic and may have limited sample size. The plan acknowledges that R² ≥ 0.85 is a target; if the dataset is too small, the model may underfit, and this limitation will be explicitly reported (see Power Analysis).
- **Causal Claims**: **None**. The study is observational. Claims are strictly about the statistical relationship between reduction percentage and texture descriptors.
- **SFE Proxy**: "Material Type" is treated as a categorical proxy for SFE. The plan acknowledges that SFE is continuous and that the GP kernel's ability to capture distinct regimes for each metal is used to model the non-linearity of the SFE-Texture relationship.
- **Metal-Specific Thresholds**: The success criterion R² ≥ 0.85 is applied per metal/descriptor. If a specific metal (e.g., Al) fails to meet this threshold due to distinct physical behavior, the cause will be analyzed rather than failing the project.

## 5. Computational Feasibility

- **Hardware**: GitHub Actions free-tier (multi-core CPU, multi-GB RAM).
- **Strategy**:
 - Use `scikit-learn`'s `GaussianProcessRegressor` (CPU-optimized).
 - Limit dataset size to a manageable scale that fits within available RAM (if necessary).
 - Avoid deep learning; use `orix` for crystallographic operations (CPU-only).
 - Total runtime target: < 4 hours to allow for CI overhead.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Missing Variables** | High | Explicitly model residual variance using Shapley values (FR-008); do not claim causality. |
| **Low Confidence Data** | Medium | Filter < 0.1 (FR-002); flag samples with >50% loss (Edge Case 3). |
| **R² < 0.85** | High | Report failure; analyze if due to missing physics (e.g., SFE differences) or data noise. Allow for metal-specific analysis. |
| **Extrapolation Errors** | Medium | Apply penalty factor (FR-009); flag as "extrapolated". |
| **Synthetic Data Tautology** | High | Implement Hold-out Physics Check to validate against known trends, not just R². |
| **SFE Proxy Bias** | Medium | Acknowledge the limitation; use GP to model non-linear regimes; report residual variance as an upper bound. |