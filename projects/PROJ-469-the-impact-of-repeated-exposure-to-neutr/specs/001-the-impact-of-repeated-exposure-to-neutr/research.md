# Research: 001-political-news-implicit-bias

## Dataset Strategy

### Verified Sources
The analysis relies on the **Project Implicit "Political IAT"** dataset.
- **Source**: Project Implicit (Public Data).
- **Verified URL**: **NO verified source found**. The provided verified datasets list contains IAT-related files from HuggingFace, but none explicitly match the "Political IAT" with `news_exposure_freq` and `political_ideology` variables required by the spec.
- **Critical Gap**: The verified list does not contain the specific dataset required for this study. The implementation MUST handle the case where the dataset is unavailable or does not match the variable requirements. The plan assumes a local file or a specific HuggingFace loader will be used if available, but strictly adheres to the "NO verified source" constraint for the specific "Political IAT" with news exposure variables if not in the list.

**Revised Dataset Strategy for Implementation**:
Since the specific "Political IAT" dataset with `news_exposure_freq` is **not** in the verified list, the code MUST:
1. Attempt to load from a user-provided path or a standard HuggingFace loader if the dataset name is known (but URL not verified).
2. **Fail gracefully**: If the data is not found or variables missing, raise `ValueError` as per FR-001.
3. **Do NOT** fabricate a URL.

*Note: The "Verified datasets" block provided contains generic IAT embeddings/policy markers, not the specific survey data with news exposure. This is a critical dataset-variable fit mismatch.*

**Dataset-Variable Fit Assessment**:
- **Required Variables**: `IAT_D_score`, `political_ideology`, `news_exposure_freq`, `age`, `gender`, `education`.
- **Verified Data Availability**: The verified list contains `davanstrien/ia_test_embeddings` (embeddings, not survey data) and `siemvaessen/iati` (IATI policy markers, not psychological IAT).
- **Conclusion**: The verified datasets **DO NOT** contain the required variables for this study. The implementation MUST rely on the user providing the correct CSV file locally or via a non-verified source, and the code MUST validate variable presence (FR-001). If the dataset is missing, the pipeline halts.

## Statistical Methodology

### Primary Model
- **Type**: Linear Regression (Ordinary Least Squares).
- **Formula**: `IAT_D_score ~ news_exposure_z * political_ideology + covariates`.
- **Framing**: **Associational only**. No causal claims.
- **Interaction**: `news_exposure_z` (z-scored) × `political_ideology` (continuous).
- **Justification**: Standard approach for testing moderation in observational psychological data.

### Robustness Checks
1. **Bootstrap**: 1000 resamples (per FR-003) to estimate stability of the interaction coefficient. **Stability Metric**: Monte Carlo Standard Error of the CI bounds to quantify bootstrap uncertainty.
2. **Alpha Sweep**: Test significance at {0.01, 0.05, 0.10} (FR-004).
3. **Covariate Adjustment**: Add `age`, `gender`, `education` to check for omitted variable bias (FR-009).
4. **Binary Ideology Split**: Re-fit model with `ideology_binary` (median split) for secondary sensitivity (FR-006).
5. **Missing Data**: MICE with 5 imputations (FR-008). Halt if >50% missingness.
6. **Missingness Sensitivity**: Delta-Adjustment analysis (varying imputation offset) to test robustness to MNAR assumptions.

### Power Analysis
- **Method**: 
  - **Prospective (Design Validation)**: Use effect size estimates from prior literature (e.g., Nosek et al. on IAT-ideology correlations) to estimate required sample size for Power ≥ 0.80 at α = 0.05. This satisfies FR-007.
  - **Retrospective (Descriptive)**: Calculate "observed power" based on observed effect size and sample size. **Note**: This is a descriptive statistic only and is not used for validation (SC-005) as it is mathematically redundant with the p-value.
- **Output**: Report prospective design adequacy (Pass/Fail) and observed power (descriptive).

### Statistical Rigor & Limitations
- **Multiple Comparisons**: Bootstrap CI provides family-wise error control for the interaction term. Alpha sweep reports sensitivity.
- **Sample Size**: Power analysis will be performed; if sample size is insufficient, the limitation will be reported in the prospective validation.
- **Causal Inference**: Explicitly framed as associational. No randomization.
- **Measurement Validity**: Assumes IAT D-score and self-reported news exposure are valid (per spec assumptions).
- **Collinearity**: `news_exposure_z` and `political_ideology` may be correlated; VIF will be checked. If definitionally related, independent effects will not be claimed.
- **Missingness**: MAR assumption tested via Delta-Adjustment sensitivity.

## Compute Feasibility

- **Environment**: CPU-only (2 cores, 7 GB RAM).
- **Constraints**:
  - No GPU.
  - Bootstrap limited to 1000 resamples (per spec); stability quantified via Monte Carlo SE.
  - MICE with 5 imputations is CPU-tractable.
  - Linear regression is fast.
- **Mitigation**: If bootstrap exceeds 6 hours, save partial state and report convergence rate.

## Decision Rationale

- **Why MICE?** Simple imputation biases variance; MICE preserves relationships (FR-008).
- **Why Bootstrap?** Interaction effects in observational data are sensitive; bootstrap provides robust CI (FR-003). Stability is quantified via Monte Carlo SE to address potential instability with 1000 resamples.
- **Why Alpha Sweep?** To demonstrate robustness of findings to arbitrary thresholds (FR-004).
- **Why No Causal Claims?** Data is observational; causal inference would require untestable assumptions not met by the data (Constitution Principle II).
- **Why Prospective Power?** Post-hoc power is tautological. Prospective analysis validates the study design using literature-based effect sizes (FR-007).
- **Why Binary Split?** To check for non-linear effects or threshold behaviors (FR-006).