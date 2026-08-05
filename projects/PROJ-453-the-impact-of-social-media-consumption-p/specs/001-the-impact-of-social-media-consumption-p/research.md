# Research: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

## Executive Summary

This research plan investigates the associational relationship between self-reported social media task-switching behavior and cognitive flexibility scores. Due to the unavailability of verified direct URLs for AddHealth, WCST, or HILDA's full cognitive modules in the provided "Verified datasets" block, the analysis will attempt to load the **HILDA** (via the verified JSON metadata for schema discovery) and **ESS** (via verified Parquet/CSV links) datasets.

**Critical Constraint**: The plan explicitly addresses the "Dataset-Variable Fit" constraint. If the verified ESS/HILDA sources lack the specific `cognitive_flexibility_score` (e.g., WCST, Trail Making) or `self_reported_switching_frequency`, the project will **HALT** with a "Data Gap" error. It will **NOT** pivot to text complexity or other proxies, as this constitutes a construct validity failure (see Section: Construct Validity & Measurement).

## Dataset Strategy

The "Verified datasets" block provides the following sources. The plan strictly adheres to these URLs and loaders.

| Dataset | Verified Source URL | Loader Strategy | Variable Fit Assessment |
|---------|---------------------|-----------------|-------------------------|
| **HILDA** | ` | `datasets.load_dataset(..., split="train")` (if JSON contains tabular data) or parse JSON metadata to identify schema. | **Critical Check**: The provided URL points to `meta.json`. This is likely a metadata file, not the full dataset. If the full HILDA data (containing cognitive scores) is not accessible via this URL or a standard `huggingface_hub` loader, the plan treats this as "NO verified source for full data" and will **HALT** with a "Data Gap" error. |
| **ESS (Parquet)** | ` | `pd.read_parquet()` | **Fit**: Likely contains survey data. Must verify presence of `age`, `screen_time` proxy, and a cognitive proxy (e.g., literacy/numeracy scores). **Note**: Numeracy is NOT a valid proxy for cognitive flexibility (set-shifting). If only numeracy is available, the plan **HALTS**. |
| **ESS (CSV)** | ` | `pd.read_csv()` (if CSV) or `read_parquet` | **Fit**: Contains "IELTS Writing Task 2 Essays". This is **NOT** a cognitive flexibility dataset. **Decision**: This dataset is **unsuitable** for the primary hypothesis. |
| **ESS (Cleaned CSV)** | ` | `pd.read_csv()` | **Fit**: Contains "Essays". **NOT** suitable for cognitive flexibility scores (WCST/Trail Making). |

**Data Availability Decision**:
The provided verified URLs for "ESS" are text/essay datasets (IELTS, EssayForum), which do **not** contain the required `cognitive_flexibility_score` (e.g., WCST) or `self_reported_switching_frequency` survey variables. The HILDA link is a `meta.json` file, likely insufficient for full analysis.
**Action Plan**:
1. **Primary Attempt**: Attempt to load the HILDA `meta.json` to see if it references a full dataset ID that can be loaded via `datasets.load_dataset("hilda")` (standard HF ID) or if it contains the necessary tabular data.
2. **Strict Halt**: If the full HILDA data (with WCST/Trail Making) is inaccessible, the project will **HALT** with a "Data Gap" error as per US-1 (Scenario 2), stating that no verified public dataset exists with both `switching_index` and `cognitive_flexibility_score` variables.
3. **No Pivots**: The plan **will not** fabricate a URL for AddHealth or WCST. The plan **will not** pivot to text analysis or use numeracy/memory as proxies for cognitive flexibility, as this violates construct validity.

*Note: For the purpose of this plan, we assume the HILDA `meta.json` links to a valid, loadable tabular dataset (e.g., via a standard HF dataset ID mentioned within) that contains the required cognitive measures. If not, the pipeline halts.*

## Construct Validity & Measurement

**Composite Index Validity**: The `switching_index` is defined as `(num_platforms) * (switching_frequency)`. This is a composite of two self-reported variables.
- **Limitation**: This product measures "media intensity" or "breadth × frequency" but does not directly measure the temporal dynamic of "task-switching behavior" (a cognitive process).
- **Mitigation**: The plan explicitly acknowledges this limitation. The sensitivity analysis (FR-005) will test the robustness of results against the individual components (`platform_count` alone, `switching_frequency` alone) to determine if the effect is driven by breadth or frequency.
- **Validation**: The plan requires that the survey instruments used for these variables be documented with their original validation sources in `data/` (Constitution Principle VI).

**Outcome Validity**: The outcome must be a validated measure of cognitive flexibility (e.g., WCST, Trail Making Test, Stroop).
- **Proxy Warning**: Using proxies like "numeracy," "memory," or "text complexity" is a **construct validity failure** because these measure different constructs (crystallized intelligence, linguistic ability) with low convergent validity with cognitive flexibility (set-shifting).
- **Decision**: The pipeline will **HALT** if the dataset lacks a validated cognitive flexibility measure.

## Statistical Methodology

### Model Specification
The primary model is a Multiple Linear Regression (OLS):
$$ Y_{flexibility} = \beta_0 + \beta_1 X_{switching} + \beta_2 X_{screen\_time} + \beta_3 X_{age} + \epsilon $$

- **Outcome ($Y$)**: `cognitive_flexibility_score` (must be continuous/interval).
- **Predictors**:
 - `switching_index`: Derived as `(num_platforms) * (switching_frequency)`.
 - `total_screen_time`: Self-reported hours.
 - `age`: Continuous.
- **Interaction**: `switching_index * age` (to test moderation).

### Statistical Rigor Checks
1. **Multiple Comparisons**: If testing multiple operationalizations (e.g., `switching_index` vs `platform_count`), apply **Benjamini-Hochberg (FDR)** correction to p-values (FR-007).
2. **Power Analysis**: Given the likely sample size ($N > 1000$ for surveys), the study is powered to detect small effects ($r \approx 0.1-0.2$) at $\alpha=0.05$. If $N < 300$, a power limitation will be explicitly stated.
3. **Causal Framing**: All results framed as "associational." No causal language ("causes", "leads to") in outputs. **Programmatic validation** will be performed on the final `interpretation` string.
4. **Collinearity**: Compute **VIF** for all predictors. If $VIF > 5$, flag "Potential Mathematical Coupling" and consider residualization of `switching_index` on `screen_time`.
5. **Measurement Validity**: Document the source of the cognitive measure and its validation evidence.
6. **Model Assumptions**:
 - **Normality**: Perform Shapiro-Wilk test on residuals.
 - **Alternative Models**: If the cognitive score is ordinal or bounded (violating OLS assumptions), switch to **Ordinal Logistic Regression** or **Poisson/Negative Binomial** models as appropriate.

### Residualization Strategy (Mathematical Coupling Mitigation)
To address the likely high correlation between `switching_index` (which includes platform count) and `total_screen_time`:
1. **Check**: Compute correlation between `switching_index` and `total_screen_time`.
2. **Threshold**: If $r > 0.7$, flag "Mathematical Coupling".
3. **Action**: Run a residualized model:
 - Regress `switching_index` on `total_screen_time` to get residuals ($R$).
 - Use $R$ as the predictor in the main model.
 - **Interpretation**: The coefficient for $R$ represents the effect of "switching intensity **independent of duration**."
4. **Justification**: This isolates the unique variance of switching not explained by total time spent, mitigating the part-whole correlation bias.

### Mean-Centering Protocol (Interaction Term)
To reduce non-essential multicollinearity in the interaction term `switching_index * age`:
- **Method**: Mean-center `switching_index` and `age` before creating the product term.
- **Justification**: This prevents the interaction term from being highly correlated with the main effects, ensuring stable coefficient estimates.

### Sensitivity Analysis
- **Alternative Definitions**: Re-run model with:
 1. `platform_count` only.
 2. `switching_frequency` only.
 3. `switching_index` (primary).
- **Thresholds**: Test median split vs. 25th/75th percentile splits for stratification.
- **Correction**: Apply FDR correction to the p-values from these sensitivity runs.

## Compute Feasibility

- **CPU-First**: The entire pipeline (pandas + statsmodels) runs on CPU. No GPU required.
- **Memory**: Streaming or chunked loading will be used if the dataset exceeds a size threshold that necessitates memory-efficient processing.
- **Runtime**: Expected completion < 1 hour for data cleaning and modeling.

## Decision Rationale

- **Dataset Choice**: HILDA is prioritized as a survey dataset likely to contain the required variables. ESS text datasets are rejected for the primary hypothesis due to variable mismatch (text vs. cognitive scores).
- **Method**: OLS regression is chosen for interpretability and alignment with the spec's "multiple linear regression" requirement, with fallback to GLM if assumptions are violated.
- **GPU**: Not needed. The analysis is purely statistical on tabular data.
- **Data Gap**: If no valid dataset is found, the project halts with a clear error rather than fabricating data or pivoting to an invalid research question.