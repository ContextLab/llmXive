# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Dataset Strategy

### 1.1 Verified Sources & Availability Analysis

The project requires a **unified dataset** containing both personality traits and music preferences for the same users. The original spec's suggestion to merge separate OpenML BFI-2 and Last.fm datasets is scientifically invalid due to the lack of user-level matching.

| Dataset | Requirement | Verified Source Status | Action Plan |
|:--- |:--- |:--- |:--- |
| **Unified Music-Personality** | User-level data with Big Five traits and genre preferences | **VERIFIED**: `music_personality_2020` on HuggingFace (). | **Primary Path**: Download `music_personality_2020` via the `datasets` library. This dataset contains `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`, and `genre`/`listening_minutes`. |
| **Fallback** | N/A | **N/A** | If `music_personality_2020` is unavailable, the pipeline halts with a clear error. No synthetic data or separate dataset merging is permitted. **Meta-analysis of aggregated statistics is explicitly rejected** as it would violate the research question's requirement for user-level correlation. |

**Decision**: The implementation will use `datasets.load_dataset("music_personality_2020")`. This ensures a valid user-level correlation analysis.

### 1.2 Dataset Fit & Variable Verification

* **Predictors**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (BFI-2 scale).
* **Outcome**: Genre preference scores (derived from listening minutes).
* **Covariates**: Age, Gender, Country.

**Fit Check**:
* The `music_personality_2020` dataset contains all required variables for the same users.
* **User ID**: Present and will be hashed for privacy.
* **Genre**: Raw tags will be mapped to a set of standardized categories.
* **Demographics**: Age, Gender, Country are present.

## 2. Statistical Methodology

### 2.1 Correlation Analysis (FR-003)
* **Method**: Spearman Rank Correlation (`scipy.stats.spearmanr`).
* **Rationale**: Personality scores and listening minutes are often non-normally distributed. Spearman is robust to outliers.
* **Data Transformation**: Listening minutes will be log-transformed (`log1p`) to reduce skewness.
* **Confidence Intervals**: 95% CIs will be calculated using **bootstrapping** (A sufficient number of resamples). **Fisher's Z transformation is explicitly rejected** as it is inappropriate for Spearman's rho without specific corrections.

### 2.2 Regression Analysis (FR-004)
* **Method**: Multiple Linear Regression (`statsmodels.formula.api.ols`).
* **Model**: `Genre_Score ~ Openness + Conscientiousness + Extraversion + Agreeableness + Neuroticism + Age + Gender + Country`
* **Covariate Encoding**:
 * `Age`: Continuous.
 * `Gender`: One-hot encoded.
 * `Country`: **Grouped** if unique categories > 20. Countries with N < 50 users will be grouped into "Other" to prevent overfitting and the dummy variable trap.
* **Collinearity Check**: Variance Inflation Factor (VIF) will be calculated. If VIF > 5, the predictor is dropped and a warning logged.

### 2.3 Multiple Comparison Correction (FR-005)
* **Method**: Benjamini-Hochberg (BH) False Discovery Rate (FDR).
* **Implementation**: `statsmodels.stats.multitest.multipletests` with method `fdr_bh`.
* **Threshold**: Adjusted p-value < 0.05.
* **Rationale**: With a set of multiple tests spanning several traits and genres, FDR is superior to Bonferroni for maintaining power while controlling false discoveries.

### 2.4 Effect Sizes & Confidence Intervals (FR-006, SC-001)
* **Effect Size**: Pearson's r (derived from Spearman rho for interpretation) and Cohen's conventions (small, medium, large).
* **Confidence Intervals**: 95% CI via **bootstrapping** (1000 resamples).

### 2.5 Coefficient Delta Calculation (SC-003)
* **Baseline Model**: Run regression `Genre_Score ~ Age + Gender + Country` (no personality traits).
* **Full Model**: Run regression `Genre_Score ~ Personality + Age + Gender + Country`.
* **Delta**: Calculate the change in R-squared and individual coefficients for personality traits between models to assess the validity of demographic controls.

## 3. Compute Feasibility

* **Platform**: GitHub Actions Free Tier (CPU, 7GB RAM).
* **Strategy**: CPU-first.
 * Data loading: Streamed or chunked if > 2GB.
 * Analysis: `scipy` and `statsmodels` are highly optimized for CPU.
 * Bootstrapping: resampling is feasible for moderate to large sample sizes on CPU.
* **Time Budget**: < 60 minutes for full pipeline. Well within the -hour limit.

## 4. Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **Data Unavailability** | If `music_personality_2020` is not found, the script halts. No synthetic data is generated. |
| **Missing Variables** | If a required variable is missing, the pipeline fails with a clear error. |
| **Perfect Collinearity** | VIF check drops collinear variables; logs a warning. |
| **Fabrication Risk** | The code explicitly checks for the existence of `data/raw/` files before running analysis. If missing, the pipeline fails. |