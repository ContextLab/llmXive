# Research: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

## 1. Dataset Strategy

The analysis requires a dataset containing:
1. **Particle Positions**: To determine geometric overlap and build the contact network.
2. **Contact Forces**: To calculate force heterogeneity and energy dissipation.
3. **Total Energy (KE/PE)**: To compute energy changes ($\Delta E$).
4. **Driving Parameters**: Wall velocity or amplitude to calculate `Work_Input`.

### Verified Datasets

The following datasets have been verified for reachability and format. **Note**: A detailed inspection of the schema of these specific files is required to confirm the presence of *granular contact forces* and *particle positions* simultaneously.

| Dataset Name | Source URL | Format | Variable Fit Assessment |
|:--- |:--- |:--- |:--- |
| `vla_demo` (Chunk 0) | ` | Parquet | **Unknown/Needs Verification**. This dataset appears to be from a Vision-Language-Action (VLA) robotics context. It likely contains robot joint states or camera frames, **not** granular particle positions/forces. **Risk of Mismatch**: High. |
| `glm52-demolition-data` | ` | JSONL | **Unknown/Needs Verification**. "Demolition" suggests structural failure, but the format (JSONL) and path (`calib`) suggest calibration data or metadata rather than raw time-series particle dynamics. **Risk of Mismatch**: High. |
| `openclaw-trajectories-demo` | ` | JSONL | **Unknown/Needs Verification**. "Trajectories" and "QA" suggest discrete task logs, not continuous granular physics simulations. **Risk of Mismatch**: High. |
| `functional_anova` | ` | JSON | **Unsuitable**. This is an *output* of a statistical analysis (ANOVA results), not raw simulation data. Cannot be used for extraction. |

### Critical Gap & Decision

**Observation**: The provided "Verified datasets" block **does not contain a confirmed source for Yade-DEM granular simulation data** with the required variables (particle positions, contact forces, energy). The listed datasets appear to be from robotics (VLA), calibration, or pre-computed statistical results.

**Decision**:
1. **Do NOT proceed with data extraction** using the provided URLs as they likely lack the required granular physics variables.
2. **Action Required**: The pipeline will be tested on **Synthetic Data** ONLY for **Code Validation** (parsing, graph construction, statistical flow).
3. **Scientific Validity**: A "simplified custom solver" using `scipy` is **methodologically infeasible** to reproduce realistic granular contact networks (force chains, non-linear friction). Therefore, **no synthetic data will be used to validate the scientific hypothesis**.
4. **Final Report Status**: If no real Yade-DEM data is provided by the user, the final report will explicitly state: **"Code Validated: Yes. Scientific Validation: Pending Real Data."** The correlation results on synthetic data will be presented as "Unit Test Results" only, not scientific findings.
5. **Future Step**: Once the pipeline is validated on synthetic data, the user must provide a valid Yade-DEM output file or a verified HuggingFace dataset containing granular contact networks.

## 2. Methodological Rationale

### Statistical Approach
- **Correlation**: Pearson (linear) and Spearman (monotonic) will be computed. Rows flagged 'ESTIMATED' or 'UNRELIABLE' (due to missing forces) will be excluded (FR-004).
- **Regression**: Generalized Least Squares (GLS) with AR(1) error structure will be used to account for temporal autocorrelation in the time-series data (FR-005). Newey-West standard errors will be used as a robustness check.
- **Robustness Checks**:
 - **Non-Linearity**: A Generalized Additive Model (GAM) check will be performed. If the GAM smooth terms are significant (p < 0.05), the linear model will be flagged, and results will be supplemented with GAM plots.
 - **Heavy-Tailed Errors**: Given the non-Gaussian nature of granular forces, **Quantile Regression** (median and 90th percentile) will be performed. If the error distribution is significantly non-Gaussian (Kolmogorov-Smirnov test p < 0.05), the Quantile Regression results will be prioritized over GLS.
- **Stationarity**: Augmented Dickey-Fuller (ADF) test (FR-010) will determine if the series is stationary. If non-stationary, the data will be segmented into fixed-length windows.
- **Multiple Comparisons**: With >5 tests (3 metrics x 2 correlations + regression), Bonferroni correction will be applied to the p-value threshold (0.01 / 5 = 0.002) to control family-wise error.

### Measurement Validity & Circularity Mitigation
- **Dissipation Definition**: To avoid circularity (where Work_Input is in the denominator of the outcome), the primary outcome for correlation is **Absolute Dissipation Rate** ($D_{abs} = Work\_Input - (\Delta KE + \Delta PE)$). The **Normalized Dissipation Rate** ($D_{norm} = D_{abs} / Work\_Input$) is calculated only as a secondary metric for steady-state efficiency checks, with explicit caveats about potential tautology.
- **Force Heterogeneity**: Defined as the Coefficient of Variation (CV) of contact forces. Cited as a validated proxy for stress distribution in Majmudar & Behringer (2005).
- **FR-009 Metrics**: To distinguish structural connectivity from force transmission:
 - **Topology-Only**: `degree_distribution_entropy` (measures the spread of connectivity without force magnitudes).
 - **Force-Only**: `force_chain_percolation` (measures the connectivity of the subgraph formed only by edges above the 90th percentile force threshold).
 - **Collinearity**: Coordination number and clustering coefficient are expected to be correlated. The analysis will report VIF (Variance Inflation Factor) and treat them as a joint descriptive set, avoiding claims of independent causal effects.

### Compute Feasibility
- **Memory**: The `extract.py` script will read the file in chunks. A **linear extrapolation** estimator (FR-008) will trigger subsampling if the estimated RAM usage exceeds 6GB.
- **CPU**: All operations (graph construction, regression, GAM, Quantile Regression) are CPU-tractable. No GPU or deep learning models are used.
- **Runtime**: The pipeline is designed to complete within 6 hours on a 2-core runner.

## 3. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Synthetic Data for Code Only** | No verified granular DEM dataset found. Synthetic data is used *only* to test pipeline logic (FR-001 to FR-010) and ensure reproducibility. **Scientific results are blocked** without real data. |
| **Absolute vs. Normalized Dissipation** | Normalized dissipation creates circularity. Absolute dissipation is used as the primary outcome to ensure predictor independence. |
| **GLS + Quantile Regression + GAM** | Standard GLS assumes Gaussian errors and linearity. Granular systems are non-Gaussian and potentially non-linear. Robustness checks are mandatory. |
| **FR-009 Metrics** | Explicitly defined to separate topology from force magnitude, addressing the tautology concern. |
| **p < 0.01 Threshold** | Adheres to Spec "Statistical Significance Thresholds" and physics literature conventions. Bonferroni correction applied for multiple tests. |
| **Verified Accuracy Gate** | Added as a mandatory step in Phase 0 and Phase 3 to satisfy Constitution Principle II before finalizing artifacts. |