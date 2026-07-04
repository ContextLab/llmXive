# Research: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Research Question

How does the choice of variable selection method (Forward Stepwise, Backward Elimination, LASSO) impact the **Inference Power** (probability of rejecting H0 with p < alpha) and **Selection Recovery** (probability of selecting the true variable) in linear regression, under varying conditions of Signal-to-Noise Ratio (SNR) and predictor sparsity?

## Background & Motivation

Variable selection is a critical step in regression modeling. Traditional stepwise methods suffer from inflated Type I error rates, while regularization methods like LASSO offer robustness. However, the impact of these methods on *statistical power* (Inference Power) under varying signal conditions is not uniformly understood. This project distinguishes between **Selection Recovery** (did we pick the right variable?) and **Inference Power** (did we find it significant?), addressing the methodological conflation concern.

## Dataset Strategy

The study relies on real-world regression datasets to provide realistic predictor covariance structures. Synthetic outcome vectors will be generated for each dataset using **bootstrapping** (resampling rows) to preserve the empirical distribution of predictors, addressing non-normality concerns.

| Dataset Source | Verified URL | Usage Strategy |
| :--- | :--- | :--- |
| **OpenML** (10 Regression Datasets) | *API Fetch (IDs 1590-1599)* | Fetch datasets by specific IDs:, 1591, 1592, 1593, 1594, 1595, 1596, 1597, 1598, 1599. If an ID fails dimensionality checks (≥100 rows, ≥3 predictors), fetch the next valid ID in sequence (e.g., 1600, 1601, etc.) until 10 valid datasets are obtained. Use rows from these datasets for bootstrapping X. |
| **SimulatedDataset** | NO verified source found | Synthetic data generated in-memory using bootstrapped X from OpenML. No external URL required. |

**Dataset Selection Criteria**:
- Must be regression tasks (continuous target).
- Must have ≥100 rows and ≥3 predictors.
- Must not exhibit perfect multicollinearity (Condition Number < 10^10).
- Must be accessible via the OpenML API.

**Handling Missing Data**:
If a dataset lacks required variables, or if the API fails, the system will retry with exponential backoff (max 3 retries) before skipping the dataset and logging a warning. If the primary 10 IDs fail, the fallback sequence is triggered.

## Methodology

### 1. Dual Metric Definition
To address the conflation of selection and inference:
- **Selection Recovery Rate**: Proportion of true non-zero coefficients that are included in the selected model.
- **Inference Power**: Proportion of true non-zero coefficients that are included in the selected model **AND** have a p-value < alpha after OLS refitting.
*Note: FR-004 and FR-009 mandate Inference Power as the primary metric. Known Limitation: Standard OLS p-values are biased post-selection; the study compares methods under this shared bias, not absolute validity.*

### 2. Simulation Design
For each of the 10 datasets:
- **Covariance Extraction**: Resample rows from the original dataset (bootstrapping) to generate X. This preserves the empirical distribution, addressing non-normality concerns.
- **Grid of Conditions**:
  - **SNR Levels**: {0.5, 1.0, 2.0, 5.0}
  - **Sparsity Levels**: {0.1, 0.2, 0.4}
 - **Simulations**: Multiple synthetic outcome vectors per (Dataset, SNR, Sparsity) tuple. (Reduced from [deferred] to ensure 6-hour feasibility on 2 vCPU).
- **Data Generation**:
  - $X \leftarrow$ Resample rows from dataset.
  - $\beta_{true}$: Sparse vector with non-zero values scaled to achieve target SNR.
  - $Y = X\beta_{true} + \epsilon$, where $\epsilon \sim N(0, \sigma^2)$ scaled to match SNR.

### 3. Variable Selection Methods
For each simulated dataset:
- **Forward Stepwise**: Add predictors one by one based on **AIC** criterion. **Early stopping**: Stop if no improvement in AIC for a consecutive sequence of steps. (Addresses computational cost concern).
- **Backward Elimination**: Remove predictors one by one based on AIC.
- **LASSO**: Fit LASSO path, select $\lambda$ via cross-validation (CV) with **fixed random seed** to ensure reproducibility of selection instability, then refit OLS on selected variables.

### 4. Power Calculation
- **Ground Truth**: Identify indices where $\beta_{true} \neq 0$.
- **Selection**: Record which variables are retained by each method.
- **Refitting**: For selected variables, fit OLS and compute p-values.
- **Metric**:
  - **Inference Power** = (Count of true non-zero coefficients with $p < \alpha$) / (Total true non-zero coefficients).
  - **Selection Recovery** = (Count of true non-zero coefficients selected) / (Total true non-zero coefficients).
- **Alpha Thresholds**: {0.01, 0.05, 0.10}.
- **Note on Post-Selection Inference**: Standard OLS p-values are used as required by the spec. We acknowledge that post-selection inference is known to be biased (anti-conservative). This is a known limitation; the study compares methods under the *same* flawed metric to evaluate relative performance, not absolute validity.

### 5. Statistical Comparison
- **Unit of Analysis**: **Individual simulation-level power estimates** (n=24,000). We do NOT aggregate to dataset-level means before testing, to preserve variance structure and meet FR-005.
- **Test**: Kruskal-Wallis H-test to compare distributions of Inference Power across methods.
- **Post-hoc**: Dunn's test with Holm correction for multiple comparisons if Kruskal-Wallis is significant.
- **Sensitivity**: Repeat analysis for each Alpha threshold.

### 6. Diagnostics
- **Collinearity**: Compute Variance Inflation Factor (VIF) or condition number for each dataset. Stored in `data/processed/diagnostics.csv`.
- **Zero Coefficients**: Explicitly handle true zero coefficients as true negatives (excluded from power denominator).

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (2 vCPU, ~7 GB RAM, no GPU).
- **Strategy**:
  - **Chunking**: Process simulations in batches of a manageable size to manage memory.
  - **Optimization**: Early stopping for stepwise; cap predictors at 200 for stepwise methods; fixed seed for LASSO CV.
  - **Pilot Run**: T024 validates that 200 sims provide sufficient CI width (< 0.1) before full run.
  - **Timeout**: Watchdog timer fails job if > 5.5 hours.
  - **Memory**: `tracemalloc` fails job if > 6.5 GB.

## Decision Rationale

- **Why OpenML?** Provides diverse, real-world covariance structures.
- **Why Bootstrapping?** Preserves empirical distribution of X, addressing non-normality.
- **Why 200 Sims?** Balances statistical stability (CI width) with 6-hour runtime constraint on 2 vCPU.
- **Why AIC?** Fixed criterion for Forward Stepwise to ensure construct validity.
- **Why Individual Unit of Analysis?** Preserves variance structure for Kruskal-Wallis, meeting FR-005.
- **Why OLS Refitting?** Required by FR-009 to calculate p-values for Inference Power.
- **Why Pilot Run?** Ensures feasibility before committing to full runtime.

## Limitations

- **Dataset Size**: Limited to datasets with ≤50,000 rows to fit in RAM.
- **SNR Range**: Fixed to low-moderate levels.
- **Selection Methods**: Only three methods tested.
- **Post-Selection Inference**: Standard OLS p-values are biased; study compares relative performance under this bias, not absolute validity.
- **Collinearity**: Perfect multicollinearity (Condition Number > 10^10) causes dataset skip.
