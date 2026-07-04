# Research: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

## Research Question
**Associational**: To what extent do mean coordination number and chemical heterogeneity **predict** the glass transition temperature ($T_g$) of chalcogenide glasses, and can their contributions be disentangled in the presence of compositional collinearity?

*Note: This is an observational study. No causal claims are made. All findings are framed as predictive associations.*

## Method
1. **Data Acquisition**: Download the supplementary dataset from the 2022 study (arXiv:2211.00691v1).
2. **Feature Engineering**: Compute mean coordination number (MCN), electronegativity variance ($\sigma_{\chi}$), and atomic radius variance ($\sigma_{r}$) from elemental compositions using the `mendeleev` library.
3. **Power Analysis**: Calculate Minimum Detectable Effect Size (MDES) for the heterogeneity term.
4. **Modeling**: Train a Gradient Boosting Regressor (GBR) and a Linear Regression baseline using `scikit-learn` with k-fold cross-validation.
5. **Collinearity Mitigation**: If VIF ≥ 5, apply **Residualization** (orthogonalize heterogeneity against MCN) to estimate unique variance.
6. **Interpretability**: Apply `shap.TreeExplainer` to the trained GBR. To satisfy memory constraints (<7 GB RAM), the dataset is sampled to ≤5000 samples if necessary.
7. **Validation**: Compute RMSE, $R^2$, VIF for collinearity, bootstrapped confidence intervals for feature importance, and **Cross-Family Transferability** metrics.

## Dataset Strategy

| Dataset Name | Source/URL | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| Chalcogenide Composition Data | arXiv:2211.00691v1 (Supplementary) | Primary data source for elemental formulas and $T_g$. | **NO verified source found**. The dataset is referenced by the study but the specific supplementary URL is not in the verified block. The system will attempt to fetch from the documented URL in the spec, with retry logic. If unreachable, the pipeline halts with `DATA_MISSING: URL_UNREACHABLE`. |
| Periodic Property Database | `mendeleev` (Python Package) | Source for electronegativity, atomic radius, coordination numbers. | **Verified**: Standard scientific library, no external URL needed. |

**Dataset-Variable Fit**:
The primary study (arXiv:2211.00691v1) reports elemental compositions and $T_g$ values.
- **Outcome**: $T_g$ (Present in source).
- **Predictors**: Elemental formulas (Present).
- **Derived Features**: MCN, $\sigma_{\chi}$, $\sigma_{r}$ (Computed from formulas).
- **Risk**: If the source lacks specific elemental breakdowns, feature engineering will fail. The system will log "DATA_MISSING" if columns are absent.

**Fallback Strategy**:
- If the URL is unreachable or the file format is not machine-readable (e.g., PDF-only), the pipeline **MUST** halt and log `DATA_MISSING: URL_UNREACHABLE` or `DATA_MISSING: FORMAT_UNSUPPORTED`. No data will be fabricated.

**Generalization Strategy**:
- **Primary**: Stratified split by chemical family.
- **Fallback**: If any family has < 10 samples in the test set, switch to **Leave-One-Family-Out (LOFO)** cross-validation for that family to ensure robust generalization estimates.
- **Transferability Test**: Train on all but one family, test on the held-out family to verify if feature importances are consistent across chemical families. If feature importances differ significantly (bootstrapped CI excludes zero), the mechanism is flagged as "Family-Specific".

## Statistical Rigor & Assumptions

### Multiple Comparison Correction
- **Method**: When comparing feature importances (e.g., $\sigma_{\chi}$ vs MCN), a Bonferroni correction or similar family-wise error rate control will be applied.
- **Rationale**: Prevents Type I errors when testing multiple hypotheses about feature contributions.

### Sample Size / Power
- **Acknowledgement**: The dataset size is estimated to be on the order of a thousand samples.
- **Power Analysis**: The plan will compute the **Minimum Detectable Effect Size (MDES)** for the heterogeneity term at [deferred] power. This quantifies the study's sensitivity limits.
- **Mitigation**: If MDES is larger than the expected effect size, the report will explicitly state "Insufficient Power to Detect Small Effects" rather than concluding "No Effect".

### Causal Inference Assumptions
- **Statement**: This is an **observational** study. All findings are **ASSOCIATIONAL**.
- **Rationale**: No randomization of composition. Claims about "determination" are framed as predictive associations, not causal mechanisms.

### Measurement Validity
- **Instruments**: `mendeleev` provides standard periodic properties.
- **Validation**: Standard values are cited from IUPAC/NIST sources within the library.

### Predictor Collinearity
- **Issue**: MCN and chemical heterogeneity may be correlated (e.g., specific elements drive both).
- **Method**: Compute Variance Inflation Factors (VIF).
- **Mitigation**: If VIF ≥ 5, **Residualization** (orthogonalize heterogeneity against MCN) will be applied. This is the specific mitigation strategy required by SC-007.
- **Validation of Orthogonalization**: Before interpreting residualized features, the plan will compute the correlation of the residualized feature with the original family label. If correlation remains high, the report will explicitly state that 'unique contribution' cannot be disentangled within that family, and the analysis will be restricted to 'global' effects only.

### SHAP Validation
- **Permutation Importance**: A permutation importance check will be performed to verify that feature importance is not an artifact of the model's bias towards deterministic inputs (since MCN and Heterogeneity are deterministic functions of composition).
- **Cross-Family Transferability**: Feature importances will be compared across families. If they differ significantly, the report will flag the mechanism as family-specific.

## Decision/Rationale: Compute Feasibility

| Component | Decision | Rationale |
| :--- | :--- | :--- |
| **Hardware** | CPU Only (2 cores, 7 GB RAM) | Free-tier CI constraint. No GPU. |
| **Model** | Gradient Boosting (scikit-learn) | CPU-tractable, no CUDA required. |
| **SHAP** | `TreeExplainer` + Sampling | `KernelExplainer` is too slow. Sampling to ≤5000 ensures <7 GB RAM usage. |
| **Precision** | float64 (default) | Avoids 8-bit/4-bit quantization (requires CUDA). |
| **Runtime** | ≤ 6 Hours | Cross-validation with a standard number of folds on a dataset of sufficient scale is well within limits. |

## References
- Lundberg, S. M., & Lee, S. I. (2017). A Unified Approach to Interpreting Model Predictions. *arXiv:1705.07874*. (NO verified source found for URL, cited by DOI).
- arXiv:2211.00691v1. (Primary study for chalcogenide data).