# Research: Correlational Analysis of Climate-Smart Agricultural Practices and Yield Stability Independent of Financial Access

## 1. Research Question & Hypothesis

**Primary Question**: Is the intensity of Climate-Smart Agricultural (CSA) practice adoption positively correlated with satellite-derived yield stability and improved food security in smallholder systems, independent of access to finance?

**Hypothesis**:
$H_0$: $\beta_{CSA} = 0$ (No association between CSA adoption and yield stability/food security after controlling for finance).
$H_1$: $\beta_{CSA} > 0$ (Positive association).

**Statistical Framework**:
- **Design**: Observational cross-sectional analysis.
- **Correction**: Bonferroni correction applied for multiple hypothesis testing (Yield Stability, Food Security, Interaction). Target family-wise error rate $\alpha_{FWER} = 0.05$. Individual test threshold $\alpha_{ind} \approx 0.0167$ (Holm–Bonferroni method).
- **Causal Framing**: Explicitly stated as **associational**. No causal claims will be made due to lack of randomization.

## 2. Data Strategy & Availability

### 2.1 Verified Datasets
Per the project's "Verified datasets" block, the following sources are available:

| Dataset | Description | Verified URL | Status |
|:--- |:--- |:--- |:--- |
| **LSMS-ISA (Malawi/Tanzania)** | World Bank survey data. | **NO verified source found** | **Critical Gap** |
| **Sentinel-2** | Satellite imagery. | **NO verified source found** | **Critical Gap** |
| **UCI Water Treatment Plant** | Generic tabular dataset with continuous variables. | ` | **Available (Structural Proxy)** |
| **CSA (parquet)** | Text abstracts. | ` | **Not Suitable** (Text vs. Tabular mismatch) |

### 2.2 Dataset Strategy & Mitigation

**Critical Distinction**: This project distinguishes between **Structural Validation** (does the code run correctly?) and **Scientific Validation** (does the hypothesis hold?).

1. **Primary Path (Structural Validation)**:
 * Load the **UCI Water Treatment Plant** dataset (or similar verified tabular dataset) as a structural proxy.
 * *Mapping*: Map UCI variables to the required schema (e.g., `CSA_Index` $\approx$ a continuous process variable, `Stability_Score` $\approx$ a target variable, `Finance` $\approx$ a control variable).
 * *Goal*: Validate that the *code* correctly performs spatial joins (simulated), feature engineering, regression with robust SE, VIF diagnostics, and sensitivity analysis.
 * *Limitation*: This validates the *pipeline*, not the *hypothesis*. **No scientific claims** about the relationship between CSA and yield stability can be made from this data.
2. **Secondary Path (Synthetic Fallback)**:
 * If no suitable real tabular dataset is found, generate a **synthetic dataset** that strictly adheres to `contracts/dataset.schema.yaml`.
 * *Constraint*: The synthetic data generation logic is **strictly decoupled** from the analysis logic (independent RNG seeds, no predefined correlation between `CSA_Index` and `Stability_Score`).
 * *Goal*: Ensure the pipeline does not crash and handles missing data/schema validation correctly.
 * *Limitation*: **No scientific claims** can be made. The report will explicitly state "Results are Structural Validation Only."
3. **Satellite Data**:
 * Since no verified Sentinel-2 source is listed, the pipeline will simulate the *structure* of satellite data (pixel coordinates, NDVI time-series) for the purpose of testing the spatial join and stability calculation logic.
 * *Note*: The "Yield Stability" metric calculated from this simulated data is not a real-world measurement.

**Conclusion**: The plan acknowledges that a full real-world execution is currently blocked by data availability. The implementation will focus on **structural validity** (does the code work if data were present?) and **statistical rigor** (is the analysis method correct?), while clearly flagging the data gap.

## 3. Statistical Methodology

### 3.1 Variable Construction
- **Predictor ($X_1$)**: `CSA_Index`. Sum of binary indicators for practices (e.g., conservation tillage, crop rotation) + extension visit frequency.
- **Outcome 1 ($Y_1$)**: `Stability_Score`. Calculated as $1 / CV(NDVI_{time\_series})$. Higher = more stable.
 * *Masking*: Exclude pixels where mean NDVI < 0.2 (fallow/early season) to prevent division by near-zero and heteroskedasticity.
- **Outcome 2 ($Y_2$)**: `HFIAS`. Household Food Insecurity Access Scale (lower = better).
- **Confounder ($Z$)**: `Access_to_Finance`. Binary/Continuous.
- **Controls ($W$)**: `Land_Size`, `Education_Level`, `Rainfall_Anomaly`.

### 3.2 Models
**Model 1 (Yield Stability)**:
$$ Stability\_Score_i = \beta_0 + \beta_1 CSA\_Index_i + \beta_2 Finance_i + \sum \beta_k W_{k,i} + \epsilon_i $$

**Model 2 (Food Security)**:
$$ HFIAS_i = \gamma_0 + \gamma_1 CSA\_Index_i + \gamma_2 Finance_i + \sum \gamma_k W_{k,i} + \epsilon_i $$

**Estimation**:
- OLS with **Robust Standard Errors** (Huber-White) to handle heteroskedasticity.
- **Collinearity Check**: Variance Inflation Factor (VIF). Threshold: VIF > 5 triggers warning.
- **Significance**: $\alpha = 0.0167$ (Bonferroni corrected).

### 3.3 Sensitivity Analysis
- **Variable**: Cloud Cover Threshold (e.g., 20%, 40%, 60%, [deferred]).
- **Metric**: Stability of $\beta_1$ (CSA_Index coefficient) across thresholds.
- **Output**: Plot of coefficient magnitude vs. threshold.

### 3.4 Model Specification Sensitivity
- **Test**: Ramsey RESET test for non-linearity.
- **Action**: If RESET p-value < 0.05, run a secondary model with:
 1. Interaction term: `CSA_Index * Access_to_Finance`.
 2. Quadratic term: `CSA_Index^2`.
- **Goal**: Detect if the linear assumption is invalid and prevent Type II errors.

## 4. Compute Feasibility & Rationale

- **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, no GPU).
- **Strategy**: **CPU-First**.
 - All statistical operations (regression, VIF) are classical and CPU-tractable.
 - Data processing (spatial join) will be performed on a **sampled** dataset or aggregated to village level to ensure memory safety (< 7 GB).
 - No deep learning or GPU-accelerated models are used.
- **Rationale**: The methodology (OLS, VIF, Bonferroni) does not require GPU acceleration. Using a GPU would be unnecessary overhead and incompatible with the runner. The "GPU escape hatch" is not needed for this specific statistical analysis.

## 5. Risk Mitigation

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **LSMS-ISA Data Unavailable** | High (No real data) | Pipeline switches to Structural Validation Mode (UCI/Synthetic). Report explicitly states "Structural Validation Only". |
| **Spatial Join Failure** | Medium (No linkage) | Fallback to village-level aggregation; log exclusion counts. |
| **Collinearity (VIF > 5)** | Medium (Model invalid) | Log warning; report includes "Collinearity Note"; consider dropping correlated predictors in sensitivity analysis. |
| **Sample Size < 1000** | Medium (Low power) | Aggregate to village level (min N=30 per village); report power limitation. |
| **Non-Linearity** | Medium (Bias) | Run Ramsey RESET; if failed, run interaction/quadratic model. |
| **Temporal Misalignment** | High (Noise) | Explicit check: `survey_reference_period` must overlap `satellite_growing_season`. |

## 6. Power Analysis & Aggregation Fallback
- **Target**: $N > 1000$ households.
- **Linkage Rate**: Acknowledged that fuzzing may reduce linkage to < 95%.
- **Fallback**: If $N_{household} < 300$, aggregate to village level.
- **Village Minimum**: Ensure $N_{village} \ge 30$ to maintain statistical power for regression. If $N_{village} < 30$, the analysis will halt with a `LOW_POWER` error.