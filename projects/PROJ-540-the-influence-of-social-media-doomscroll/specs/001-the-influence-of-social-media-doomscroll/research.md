# Research: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Research Question

Does the frequency of negative news consumption on social media **associate with** elevated anxiety scores, independent of demographic factors?

**Note**: Due to the cross-sectional nature of the data, all claims will be framed as **associational**, not causal. The term "predict" in the hypothesis refers to statistical prediction (variance explained), not causal direction.

## Theoretical Background

"Doomscrolling" refers to the tendency to continuously scroll through negative news on social media platforms, potentially exacerbating anxiety. Anticipatory anxiety is the worry or fear about future events. While the mechanism is often discussed in media, empirical evidence linking specific consumption frequencies to anxiety scores, controlling for baseline traits, requires rigorous statistical analysis.

## Dataset Strategy

### Primary Dataset Selection

**Target**: NHANES 2017-2018 (National Health and Nutrition Examination Survey).

**Verified Sources**:
- **NHANES 2017-2018**: Available via the official CDC NHANES FTP or verified HuggingFace mirrors.
  - URL: `https://wwwn.cdc.gov/nchs/nhanes/ContinuousNhanes/Default.aspx?BeginYear=2017` (Official) or verified HuggingFace dataset `nhanes_2017_2018` (if available and verified).
  - **Variables**: Contains 'GAD-7' (Generalized Anxiety Disorder 7-item scale) for anxiety, 'Media Exposure' variables for news consumption, and demographic covariates (Age, Gender, Education).
  - **Suitability**: **Conditional**. The dataset contains 'general anxiety' (GAD) but not 'anticipatory anxiety'. Per FR-008, 'general anxiety' will be used as a proxy. The 'news exposure' variable will be proxied by available 'media consumption' variables.

**Dataset Strategy Table**:

| Dataset Name | Source URL | Variables Available | Suitability |
| :--- | :--- | :--- | :--- |
| NHANES 2017-2018 | `https://wwwn.cdc.gov/nchs/nhanes/ContinuousNhanes/Default.aspx?BeginYear=2017` | `GAD7`, `MEDNEWS`, `AGE`, `RIAGENDR`, `INDFMPIR`, `RIDRETH1` | **Conditional**: 'GAD7' used as proxy for 'anticipatory_anxiety'. 'MEDNEWS' used as proxy for 'news_exposure_freq'. |

*Note: No other open, verified source for GSS/Pew with these specific variables was provided. NHANES is the best available open dataset for this analysis.*

### Variable Mapping

| Spec Variable | Potential Dataset Column | Validation Check |
| :--- | :--- | :--- |
| `news_exposure_freq` | `MEDNEWS` (Media Exposure) | Must be numeric or ordinal. |
| `anxiety_score` | `GAD7` (Generalized Anxiety Disorder 7-item scale) | Must be numeric. |
| `baseline_anxiety` | *Not available as distinct measure* | If no distinct baseline measure exists, this covariate will be dropped to avoid coupling. |
| `age` | `AGE` | Numeric. |
| `gender` | `RIAGENDR` | Categorical. |
| `social_media_engagement` | *Not available* | Replaced by `Education Level` for robustness check. |

### Data Hygiene & Missing Data

- **Strategy**: Listwise deletion.
- **Threshold**: If resulting N < 30, halt with power warning (FR-002).
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to inspect schema and count rows. If N > 100,000, take a **random sample** of [deferred] rows (seeded) to ensure CPU feasibility and avoid selection bias. Stratified sampling will be used if the dataset is ordered by date/region.

### Construct Validity Limitation

The hypothesis requires "Anticipatory Anxiety". The available dataset (NHANES) measures "General Anxiety" (GAD-7). These are distinct constructs (State/Specific vs. Trait/General). The analysis will proceed using GAD-7 as a proxy, but the results are explicitly limited by this construct mismatch. No claim of equivalence is made.

## Statistical Methodology

### Model Specification

**Primary Model**: Multiple Linear Regression (OLS)
$$ \text{Anxiety}_i = \beta_0 + \beta_1(\text{NewsFreq}_i) + \beta_2(\text{Age}_i) + \beta_3(\text{Gender}_i) + \epsilon_i $$
*(Note: 'Baseline Anxiety' is omitted if not distinct from Outcome Anxiety to avoid mathematical coupling.)*

- **Dependent Variable**: `anxiety_score` (GAD-7)
- **Independent Variables**: `news_exposure_freq` (Media Exposure proxy), `age`, `gender`.
- **Assumption**: Linearity, Homoscedasticity, Normality of Residuals, No Multicollinearity.

### Rigor & Validation

1.  **Mathematical Coupling Check**: Verify `baseline_anxiety` and `anxiety_score` are distinct. If they are the same instrument or timepoint, drop `baseline_anxiety` from the model and flag (Edge Case 3).
2.  **Multicollinearity**: Calculate Variance Inflation Factor (VIF). If VIF > 10 for any predictor, flag model as unstable (Edge Case 3).
3.  **Multiple Comparisons**: Only one primary hypothesis test (coefficient of `news_exposure_freq`). No family-wise error correction needed unless multiple outcomes are tested (not in scope).
4.  **Power Analysis**:
    - If N < 30: Hard Stop.
    - If 30 ≤ N < 100: Proceed with "Low Power" warning.
    - Post-hoc power will be calculated based on observed effect size and N.
5.  **Causal Inference**: The study is observational. All claims will be framed as **associational**, not causal.

### Robustness Check (FR-006)

- **Condition**: Re-run model on a subset of users with **High Education** (Top 25th percentile of education level) vs. Low Education.
- **Pre-condition**: Ensure sufficient sample size in the subgroup (N ≥ 30).
- **Metric**: Compare coefficient sign and significance (p-value) between the full sample and the high-education subset.
- **Deviation Note**: The original spec required a check on 'social_media_engagement' (r > 0.3). This variable is unavailable. The check was substituted with 'Education Level' due to data constraints.
