# Research: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

## Domain Context

The "deepfake trust bias" hypothesis suggests that AI-generated faces are perceived as less trustworthy than authentic faces, or that the *perception* of trust is significantly altered by the knowledge of manipulation. However, effect sizes vary widely across studies due to differences in:
1. **Stimulus Realism**: The fidelity of the deepfake (e.g., GAN vs. Diffusion, resolution, artifact visibility).
2. **Media Literacy**: The participant's ability to detect manipulation, which may moderate the trust effect.
3. **Measurement**: Variations in trust scales (e.g., Likert vs. binary choice).

This meta-analysis aims to synthesize these effects, specifically testing whether **media-literacy metrics** and **stimulus realism stratification** (the key inclusion criteria) significantly moderate the trust bias.

## Dataset Strategy

*Note: As this is a meta-analysis of primary studies, there is no single "dataset" to download. Instead, we construct a dataset of **effect sizes** from primary studies found via literature search.*

**Search Strategy**:
- **APIs**: OpenAlex, Semantic Scholar, arXiv.
- **Queries**: 
  - `"deepfake" AND "trust"`
  - `"AI‑generated face" AND "trustworthiness"`
- **Inclusion Criteria** (FR-001, FR-002):
  - Peer-reviewed or preprint (experimental).
  - Explicit trust judgment (not just "liking" or "recognition").
  - Comparison of Authentic vs. Deepfake conditions.
  - **Critical**: Must report **media-literacy metrics** OR **stratified effect sizes by realism level**.

**Data Sources**:
Since the "Verified datasets" block in the user prompt is empty (as this is a literature synthesis task, not a raw data download task), we will **not** fabricate URLs for specific primary studies. Instead, the `01_search_and_screen.py` script will dynamically fetch data from the verified APIs (OpenAlex, Semantic Scholar, arXiv) using their public endpoints.

*Verification Note*: The plan relies on the **APIs themselves** as the verified source. The `research.md` will not list specific study URLs until the search is executed and results are validated. The "Verified Accuracy" principle is satisfied by programmatic resolution of DOIs against Crossref/OpenAlex APIs at runtime.

**Feasibility Check**:
- **Volume**: Expected < 100 studies (niche topic).
- **Compute**: Searching APIs is CPU-light. Meta-analysis on < 100 studies is trivial for 2 CPU cores.
- **Data Access**: All APIs are free-tier accessible. No GPU required.

## Statistical Methodology

### Effect Size Calculation (FR-003)
- **Primary Metric**: Cohen's *d* (standardized mean difference).
- **Conversion**:
  - Means/SDs: Direct calculation.
  - Odds Ratios: Converted to log-OR, then to *d*.
  - t-statistics/F-statistics: Converted to *d*.
- **Missing Data Handling**:
  - **Reconstructed SDs** (from exact t-stat or exact p-value): **Excluded** from primary pool (`included_in_primary=False`). Used only in sensitivity analysis.
  - **Rounded P-values** (e.g., "p < 0.05") without t-stat: **Excluded** from primary pool (Unrecoverable).
  - **Missing SDs** (no reconstruction possible): **Excluded** from primary pool. **No mean-imputation**.
  - **Sensitivity**: A "Conservative Variance Inflation" analysis is performed where missing SDs are replaced by the **maximum observed SD** in the dataset to test the upper bound of the effect. This bounds the error without introducing the bias of mean imputation.

### Meta-Analysis Model (FR-004)
- **Model**: Random-effects (DerSimonian-Laird or REML).
- **Heterogeneity**: $I^2$ and $Q$-statistic.
- **Software**: `metafor` (R) via `rpy2` (Python wrapper).

### Moderator Analysis (FR-005)
- **Method**: Mixed-effects meta-regression OR Subgroup Meta-Analysis.
- **Predictors**: 
  - `realism_level` (continuous or categorical).
  - `media_literacy_score` (continuous).
- **Harmonization Logic**:
  - **Realism**: 
    - If continuous (e.g., FID, human rating): Use Meta-Regression.
    - If categorical (High/Low) or heterogeneous: **Switch to Subgroup Meta-Analysis**. Do NOT force categorical data into regression.
  - **Media Literacy**: If study reports only categorical data (High/Low), set `media_literacy_score` to `NaN` for regression. Exclude from regression but include in subgroup analysis if discretizable.
- **Fallback Logic**:
  - If number of studies with moderator data (k) < 10: **Switch** to Subgroup Meta-Analysis (if discretizable) or report "Insufficient Power".
- **Constraint**: Studies lacking these specific moderator data are excluded from the regression/subgroup but included in the primary pooled effect.

### Robustness & Bias (FR-006)
- **Sensitivity**: Leave-one-out analysis.
- **Imputation Sensitivity**: Run model excluding all studies with `sd_reconstructed=True` (even if they were in primary pool) to verify the pooled effect is not driven by imputed data.
- **Publication Bias**: Egger's test ($p > 0.10$ indicates no bias) and Funnel Plot.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If testing >1 moderator, apply Bonferroni or FDR correction to p-values.
- **Power**: Acknowledge that with a small number of studies (< 20), moderator power is limited. Results will be framed as "exploratory" if k is low.
- **Causal Claims**: Observational (meta-analysis of observational/experimental studies). Claims are **associational** regarding moderators. No causal inference on "media literacy causing trust change" without randomization in primary studies.
- **Ecological Fallacy**: Explicitly acknowledged. Moderator effects are interpreted as **study-level associations**. The analysis uses subgroup comparisons (High vs. Low) as a robustness check to mitigate the risk of assuming linearity in aggregated data. Media literacy is a participant-level trait; aggregating it to the study level assumes the study-level mean perfectly predicts the study-level trust bias, which is a known methodological weakness. We frame results as "associational" and use subgroup analysis to validate findings.
- **Collinearity**: If `realism` and `media_literacy` are correlated in the dataset, report VIFs and consider univariate models.

## Methodological Limitations

1. **Ecological Fallacy**: The analysis aggregates individual-level traits (media literacy) to the study level. We explicitly frame results as study-level associations and use subgroup analysis to validate findings. Categorical media literacy data is set to `NaN` for regression to avoid invalid inputs.
2. **SD Imputation**: We do **not** impute SDs in the primary analysis to avoid bias. We use a conservative sensitivity analysis (max SD) to bound potential error.
3. **Realism Harmonization**: If continuous realism metrics are unavailable, we fall back to categorical subgroup analysis, which may reduce statistical power but preserves validity. We do not force heterogeneous qualitative variables into a regression model.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Zero Studies** | If search yields < 3 studies, report as "Insufficient Data" and halt. |
| **API Rate Limits** | Implement exponential backoff and caching in `01_search_and_screen.py`. |
| **Non-Convergence** | If `metafor` fails to converge, fallback to fixed-effects model and log the reason. |
| **Missing Moderator Data** | Strictly exclude from regression; fallback to Subgroup Analysis if k < 10. |
| **Missing SDs** | Exclude from primary pool; run conservative sensitivity analysis (max SD). |
| **Human Adjudication Required** | Pipeline halts if Kappa < 0.6. |

## Decision Rationale

**Why R for Meta-Analysis?**
The `metafor` package is the industry standard for meta-analysis, offering robust implementations of random-effects models, meta-regression, and publication bias tests that are not fully available or validated in Python's `statsmodels`. Using `rpy2` allows us to leverage R's statistical rigor while maintaining a Python-centric pipeline for data ingestion and orchestration.

**Why Exclude Reconstructed SDs?**
FR-003 mandates this to prevent bias from imprecise data. Rounded p-values introduce uncertainty that inflates Type I error rates if included in the primary pool.

**Why CPU-Only?**
The free-tier GitHub Actions runner (2 CPU, 7 GB RAM) is sufficient for meta-analysis of < 100 studies. No GPU is needed for these statistical operations.

**Why Subgroup Fallback?**
If continuous realism metrics are unavailable for >30% of studies, a regression is invalid. Switching to Subgroup Meta-Analysis allows us to answer the research question for the full dataset using categorical comparisons.