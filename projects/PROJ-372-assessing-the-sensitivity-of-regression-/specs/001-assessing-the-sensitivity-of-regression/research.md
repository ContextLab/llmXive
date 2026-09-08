# Research: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Objective
To empirically determine how the standard deviation of OLS regression coefficients varies with dataset subset size and the severity of OLS assumption violations (heteroscedasticity, multicollinearity, outliers), while rigorously controlling for sample size and baseline data quality.

## Methodology

### 1. Data Ingestion & Profiling (US1)
- **Source**: Verified open datasets from HuggingFace/UCI (see Dataset Strategy).
- **Profiling Metrics (Full Dataset)**:
 - **Multicollinearity**: Condition Number of the design matrix ($X^T X$).
 - **Heteroscedasticity**: Breusch-Pagan test statistic and p-value.
 - **Outliers**: Mean Cook's Distance across observations.
- **Severity Classification**:
 - **Low**: BP p-value > 0.10
 - **Medium**: 0.05 < BP p-value <= 0.10
 - **High**: BP p-value <= 0.05
- **Output**: `DatasetProfile` JSON artifact (stored in `artifacts/profiles/`).
- **Constraint**: These metrics are computed **ONCE on the full dataset** and stored. They serve as **random intercepts** in the meta-analysis to control for baseline dataset quality, but are **NOT** used as the primary predictors for subset stability to avoid tautology.

### 2. Subset Resampling (US2)
- **Strategy**: Random sampling without replacement.
- **Tiers**: Percentages of the full dataset size defined in `config.yaml`: `[10, 25, 50, 75, 90]`.
- **Iterations**: 200 random subsets per tier.
- **Per-Subset Profiling**: For **each subset**, the OLS model is fit, and **Subset-Specific** Condition Number, Breusch-Pagan p-value, and Cook's Distance are computed. These are the **primary predictors** for the meta-analysis.
- **Convergence Check**:
 - **Method**: Bootstrap Resampling. We resample the coefficient estimates repeatedly (e.g., 1000 bootstrap resamples) to derive an empirical distribution of the Standard Error (SE) of the SD.
 - **Criterion**: If the 95% Confidence Interval of the SE of the SD exceeds 5% of the SD, the tier-dataset combination is flagged as **"Invalid"**.
 - **Validity Gate**: If a tier is marked "Invalid", it is **excluded** from the final meta-analysis. The precision claim is invalidated for that tier, and the result is not reported in the final curves. This ensures that only statistically valid estimates contribute to the findings, resolving the "cosmetic log entry" flaw.
- **Model**: Ordinary Least Squares (OLS) fit on each subset.

### 3. Meta-Analysis (US3)
- **Dependent Variable**: Empirical Standard Deviation of coefficients per tier (aggregated).
- **Independent Variables**:
 - **log(N)**: Continuous control variable derived from the tier percentage (log of actual sample size). This deconfounds the sample size effect (1/sqrt(N)) from the violation effect.
 - **Subset_CondNum**: Condition Number computed **per subset**.
 - **Subset_BP_p**: Breusch-Pagan p-value computed **per subset**.
 - **Subset_Cooks_D**: Mean Cook's Distance computed **per subset**.
 - **Interaction Terms**: Subset_CondNum × Subset_BP_p (and others if non-collinear).
 - **Random Intercept**: Full_Dataset_CondNum (or Dataset ID) to control for baseline dataset properties.
- **Method**: Hierarchical Linear Model (HLM) with random intercepts for Dataset ID. This allows pooling across datasets while accounting for dataset-specific baselines. The model formula is: `Stability ~ log(N) + Subset_CondNum + Subset_BP_p + Subset_Cooks_D + (1 | Dataset_ID)`.
- **Output**: Stability curves (Coefficient SD vs. Subset_CondNum, stratified by Severity) and regression coefficients indicating the sensitivity of instability to **subset-specific** violations.
- **Validity**: By using Subset-Specific predictors and controlling for log(N) and Full-Dataset baselines, the analysis isolates the effect of subset selection on stability, avoiding the tautology of regressing Subset Stability on Full-Dataset properties.

## Dataset Strategy

The project relies exclusively on **open, directly-downloadable datasets** verified for reachability and suitability for OLS regression (tabular, numerical).

| Dataset Name | Source / Verified URL | Usage | Notes |
|:--- |:--- |:--- |:--- |
| **UCI Census Income (94)** | ` | Primary | Contains numerical and categorical features suitable for OLS after encoding. |
| **UCI Wine Quality (Red)** | `https://huggingface.co/datasets/UCI/wine-quality-red/resolve/main/winequality-red.csv` | Secondary | Tabular numerical data with continuous target, ideal for OLS. |
| **UCI Concrete Compressive Strength** | `https://huggingface.co/datasets/UCI/concrete-compressive-strength/resolve/main/concrete_data.csv` | Tertiary | Tabular numerical data with continuous target, suitable for OLS. |

**Note**: `DatasetProfile` is an internal artifact, not a dataset. No URL is cited for it.
**Removed**: UCI DROP and UCI HAR datasets were removed as they are NLP/Time-Series datasets unsuitable for OLS without unverified, complex feature engineering.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: The meta-analysis involves multiple predictors. We will report uncorrected p-values but explicitly state the exploratory nature. If formal hypothesis testing on the interaction is required, a Bonferroni correction will be applied, though the primary goal is estimation of effect sizes.
- **Power Limitation**: With multiple subsets per tier, the SE of the SD is estimated via Bootstrap. If the 95% CI of the SE exceeds 5% of the SD, the result is flagged as "Invalid" and excluded. The 200 subset count is fixed by the research design; if convergence fails, the precision is unknown and the result is not reported.
- **Causal Claims**: All findings are **associational**. We are observing how subset selection *correlates* with instability given violation severity. We do not claim that violations *cause* instability in a causal sense without further experimental design, though this is the theoretical expectation.
- **Collinearity**: If predictors in the meta-analysis are highly correlated (e.g., Subset CondNum and Subset BP), we will report Variance Inflation Factors (VIF) and acknowledge the limitation in interpreting independent effects.
- **Circularity Prevention**: The analysis explicitly separates **Baseline Properties** (Full Dataset CondNum, used as random intercept) from **Subset Outcomes** (Stability computed on subsets) and **Subset Predictors** (CondNum, BP, Cook's computed per subset). This ensures the predictor is not derived from the full dataset in a way that creates circular reasoning with the outcome.

## Compute Feasibility Decision

- **Method**: OLS on subsets.
- **Platform**: CPU (GitHub Actions Free Tier).
- **Rationale**: OLS is $O(N \cdot p^2)$ or $O(N \cdot p^3)$. For typical datasets (N < 100k, p < 100), this is trivial on multiple CPU cores. No GPU is required for this specific statistical method. The "GPU escape hatch" is not needed for this specific statistical method.
- **Memory**: Streaming will be used for datasets > 7GB to stay within the 7GB RAM limit.