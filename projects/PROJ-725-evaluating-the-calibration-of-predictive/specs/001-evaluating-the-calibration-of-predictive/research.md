# Research: Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks

## 1. Dataset Strategy

### Verified Datasets
The plan relies on a **dynamic selection strategy** targeting **public regression benchmarks** from OpenML. The `openml` Python library is used to fetch datasets where the task type is explicitly "regression" and the target variable is continuous. This ensures programmatic download on the CI runner without authentication and guarantees the presence of a valid regression target.

| Dataset Selection Criteria | Source URL/ID | Type | Notes |
| :--- | :--- | :--- | :--- |
| **OpenML Regression Tasks** | `openml.datasets.get_dataset(task_id=...)` | Regression | Auto-selected from a predefined list of stable regression benchmarks (e.g., IDs 41147, 41143, 41163) or dynamically fetched based on metadata. The "Verified" status applies to the OpenML metadata guaranteeing a continuous target, not a specific URL. |

**Critical Feasibility Note**: 
- **Dynamic Selection**: The study targets N=10 datasets. The `data/loader.py` will query OpenML for datasets matching the regression criteria. If fewer than 5 valid datasets are found, the study scope is reduced to "Available Regression Benchmarks" and the statistical power analysis (permutation test) is adjusted to reflect the actual N (see Power Analysis below).
- **No New Datasets**: No datasets will be invented or guessed. If the OpenML query fails to return sufficient regression data, the study is flagged as "Data Insufficient" for the full scope.
- **Streaming Strategy**: To respect the 7 GB RAM limit, `openml` is used with `download_data=False` initially to inspect metadata, then data is downloaded in shards or via `streaming=True` where supported.

### Data Preprocessing
1. **Target Validation**: Before splitting, the loader checks if the target column is continuous (numeric). If not, the dataset is skipped and logged.
2. **Cleaning**: Drop rows with missing targets (FR-001 edge case).
3. **Split**: 70/30 split with fixed seed (FR-001).
4. **Validation**: Check sample size. If test set < 50, flag as "Insufficient for Beta-Binomial Test" (Edge Case).

### Power Analysis
- **Permutation Test**: Requires N >= 5 datasets to have meaningful power. If N < 5, the pairwise comparison test is skipped, and results are reported as descriptive statistics only.
- **Binomial/Beta-Binomial**: Requires test set size >= 50 for stable p-value estimation. If smaller, the significance test is skipped and the coverage rate is reported with a confidence interval.

## 2. Methodology & Statistical Rigor

### Uncertainty Quantification Methods
1.  **Quantile Regression (QR)**:
    *   *Implementation*: `sklearn.ensemble.GradientBoostingRegressor` with `loss='quantile'` (alpha=0.05, 0.95).
    *   *Rationale*: Non-parametric, handles heteroscedasticity well.
2.  **Bayesian Linear Regression (BLR)**:
    *   *Implementation*: `sklearn.linear_model.BayesianRidge`.
    *   *Rationale*: Fast, closed-form posterior, assumes homoscedastic Gaussian noise (good baseline for comparison).
3.  **Gaussian Process Regression (GPR)**:
    *   *Implementation*: `sklearn.gaussian_process.GaussianProcessRegressor` with RBF kernel.
    *   *Rationale*: Exact inference provides calibrated intervals *if* the kernel is correct.
    *   *Feasibility*: Limited to datasets with N < 2000 to avoid O(N^3) memory blowup on 7 GB RAM. Larger datasets trigger a "Skip GP" fallback.
4.  **Split Conformal Prediction (SCP)**:
    *   *Implementation*: Standard split conformal using a base estimator (e.g., Random Forest) and calibration set quantile.
    *   *Rationale*: Distribution-free, guaranteed marginal coverage.

### Statistical Tests (FR-005, SC-003)
1.  **Beta-Binomial Test**:
    *   *Null Hypothesis ($H_0$)*: The *true* coverage equals the nominal coverage (0.90), with over-dispersion modeled.
    *   *Method*: Fit a Beta-Binomial distribution to the coverage outcomes across the test set, estimating the dispersion parameter $\phi$. Test if the mean of the distribution equals the nominal coverage.
    *   *Correction*: Bonferroni correction applied across all method-dataset-bin combinations to control Family-Wise Error Rate (FWER).
    *   *Output*: p-value, "Mis-calibrated" flag (if p < 0.05/FWER), and estimated dispersion parameter $\phi$.
    *   *Rationale*: Replaces the Binomial Test to account for potential correlation in prediction errors (e.g., due to model structure or data clustering), avoiding inflated Type I errors.
    *   *Clarification on Circularity*: For methods like QR and BLR, there is no theoretical guarantee of 0.90 coverage. The test evaluates whether the *empirical* coverage deviates significantly from 0.90, acknowledging that the "nominal" is a hyperparameter. For SCP, the test validates the theoretical guarantee.
2.  **Permutation Test (Pairwise)**:
    *   *Method*: Monte Carlo permutation (10,000 iterations) on the vector of coverage differences between Method A and Method B.
    *   *Rationale*: N=10 (or fewer) is too small for asymptotic normality assumptions of t-tests.
    *   *Limitation*: With N=10, the p-value resolution is limited (min p-value ~0.001). The test is designed to detect large effect sizes; marginal results must be interpreted with caution. If N < 5, this test is skipped.
3.  **Interval Score**:
    *   *Formula*: $S = (U - L) + \frac{2}{\alpha} (L - y) \mathbb{I}(y < L) + \frac{2}{\alpha} (y - U) \mathbb{I}(y > U)$.
    *   *Usage*: Lower score = better (sharpness + calibration).

### Heteroscedasticity Analysis (FR-006, SC-004)
1.  **Robust Baseline Variance Model**: Train a secondary model (e.g., squared residual regression using a simple Ridge regression) on the training set **independently** of the primary UQ methods being evaluated. This model predicts $\sigma^2(x)$ using a robust link function to avoid contamination by the primary method's errors.
2.  **Stratification**: Bin test points into Low/Med/High variance based on the **independent** variance model's predictions.
3.  **Metric**: Compare coverage rates across bins. A valid method should have consistent coverage across bins.
    *   *Rationale*: This resolves the circular dependency where the variance model was previously trained on the residuals of the method being tested. The stratification is based on the *predicted* variance from an independent model, and the analysis is interpreted as "conditional coverage given the independent model's variance estimate".

### Sensitivity Analysis (FR-007, SC-005)
1.  **Sweep**: Re-evaluate "Mis-calibration" counts for thresholds $\delta \in \{1\%, 2\%, 3\%\}$.
2.  **Reporting**: Plot/Tabulate the count of flagged datasets vs. threshold to demonstrate robustness.

## 3. Compute Feasibility

- **CPU-First**: All methods (QR, BLR, GPR, SCP) are CPU-tractable for small/medium datasets (N < 2000).
- **Memory Management**:
  - GPR is capped at N=2000. If a dataset exceeds this, the plan logs a warning and skips GPR for that dataset (Edge Case).
  - Data is loaded via `pandas` with `dtype` optimization to fit within available memory constraints.
- **No GPU Required**: The spec explicitly assumes CPU-only. The methods selected do not require CUDA.

## 4. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **OpenML Dynamic Selection** | Ensures verified regression targets and N=10 statistical power. Replaces unreliable HF CSV mirrors. |
| **Beta-Binomial over Binomial** | Accounts for over-dispersion and correlation in prediction errors, avoiding invalid p-values. |
| **Permutation over Wilcoxon** | Sample size (N=10) violates Wilcoxon assumptions; permutation is exact for any N. |
| **Independent Variance Model** | Resolves circular dependency in heteroscedasticity analysis by using a robust baseline model. |
| **Low Power Acknowledgment** | Explicitly states the limitation of permutation tests with N=10 to prevent over-interpretation of marginal results. |
| **Skip GP on Large Data** | O(N^3) complexity is fatal on 7 GB RAM. Skipping is better than crashing or fabricating results. |
| **Fixed 70/30 Split** | Standard practice; ensures consistency across methods. |
| **Target Validation** | Prevents pipeline failure on datasets with non-continuous targets. |