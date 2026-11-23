# Analysis Specification: Doomscrolling and Anxiety

## 1. Research Question

Does frequent exposure to negative news on social media (doomscrolling) predict higher levels of anticipatory anxiety, independent of baseline anxiety traits?

## 2. Data Variables

| Variable | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `news_exposure_freq` | Continuous | Frequency of consuming negative news on social media (1-5 scale) | Survey Item |
| `anxiety_score` | Continuous | Score on anticipatory anxiety scale | Survey Item |
| `baseline_anxiety` | Continuous | General anxiety trait score (control) | Survey Item |
| `age` | Integer | Age of respondent | Survey Item |
| `gender` | Categorical | Gender identity | Survey Item |
| `social_media_engagement` | Continuous | General engagement metric (for robustness) | Survey Item |

## 3. Statistical Model

### Primary Model
$$
\text{anxiety\_score}_i = \beta_0 + \beta_1(\text{news\_exposure\_freq}_i) + \beta_2(\text{baseline\_anxiety}_i) + \beta_3(\text{age}_i) + \beta_4(\text{gender}_i) + \epsilon_i
$$

### Assumptions
1. **Linearity**: Linear relationship between predictors and outcome.
2. **Homoscedasticity**: Constant variance of residuals (checked via Breusch-Pagan).
3. **Normality**: Residuals are normally distributed (checked via Shapiro-Wilk).
4. **No Multicollinearity**: VIF < 5 for all predictors.

## 4. Validity Checks

- **Construct Validity**: `baseline_anxiety` and `anxiety_score` must be statistically distinct to avoid mathematical coupling. The system must raise `MathematicalCouplingError` if they are identical or perfectly correlated.
- **Power Check**: Analysis halts if sample size $N < 30$ after cleaning.

## 5. Robustness Strategy

If `social_media_engagement` correlates with `news_exposure_freq` ($r > 0.3$), the model is re-fitted on the top 25th percentile of engagement to test for effect stability in heavy users.

## 6. Output Artifacts

- `outputs/regression_results.json`: Coefficients, p-values, R-squared.
- `outputs/correlation_results.json`: Pairwise correlations.
- `outputs/robustness_results.json`: Comparison of full vs. subset models.
- `outputs/plot.png`: Scatter plot with regression line.
- `outputs/final_report.md`: Narrative summary of findings.
