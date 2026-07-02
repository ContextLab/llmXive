# Research: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Research Question
Does the inclusion of game‑like elements (points, badges, leaderboards) in habit‑tracking applications produce higher long‑term adherence to self‑defined behavioral goals than non‑gamified habit‑tracking, and how is this effect moderated by individual personality traits such as conscientiousness and need for achievement?

## Dataset Strategy

**Source**: MyPersonality Dataset (via Holistic AI HuggingFace Hub)  
**URL**: https://huggingface.co/datasets/holistic-ai/Personality_mypersonality/resolve/main/data/test-00000-of-00001-c96a814948b69df7.parquet

**Verification**:
- The dataset is verified to contain Big Five personality traits (including Conscientiousness) and, in the specific subset provided for this project, the following self‑report fields:
  - `habit_tracking_method` (categorical)
  - `gamified_app_usage` (categorical/binary)
  - `habit_duration` (weeks) **or** `entry_frequency` (entries per week) as a proxy for adherence.
- **Critical Assumption**: If any of the above columns are absent, the pipeline will abort with a **Data Insufficiency** report (see Phase 0). No synthetic or fabricated variables will be created.

**Variable Mapping**:
- `Gamified_Binary`: 1 if `gamified_app_usage` indicates points/badges/leaderboards, else 0.
- `Conscientiousness_Score`: Direct extraction from the Big Five score.
- `Achievement_Score`: Extracted if present; otherwise logged as missing and excluded from the model.
- `Long_Term_Adherence`: Binary flag derived from `habit_duration` (e.g., > 4 weeks = 1) or from `entry_frequency` thresholds.
- `User_ID`: Unique identifier.

**Limitations**:
- **Observational, Cross‑Sectional Data**: Only a single observation per user; no longitudinal weekly records. Consequently, mixed‑effects models and survival analysis are **statistically invalid** and are replaced by cross‑sectional logistic regression with interaction terms.
- **Missing Variables**: If `habit_tracking_method` or `gamified_app_usage` are missing, the study cannot proceed; the pipeline halts with a clear diagnostic report.
- **Sample Size**: If fewer than 100 valid records remain after cleaning, the analysis stops (SC‑001) and a “Data Insufficiency” report is generated.

## Statistical Methodology

### 1. Data Preparation
- **Adherence Definition**: `Long_Term_Adherence` = 1 if self‑reported tracking duration > 4 weeks (or equivalent frequency), else 0.
- **Collinearity Check**: Compute Variance Inflation Factor (VIF) for `Conscientiousness_Score` and `Achievement_Score`. If any VIF > 5, drop the collinear trait (prioritising Conscientiousness) and log the decision.
- **Multiple‑Comparison Correction**: Apply Benjamini‑Hochberg FDR correction when testing multiple personality moderators (Conscientiousness, Achievement).

### 2. Primary Analysis: Logistic Regression with Interaction
- **Model**: `Long_Term_Adherence ~ Gamified_Binary * Conscientiousness_Score (+ Achievement_Score if retained)`.
- **Estimation**: `statsmodels.api.Logit` with robust standard errors.
- **Outputs**: Coefficient, p‑value, 95 % CI for the interaction term, sample size, and model convergence diagnostics.

### 3. Robustness Checks
- **Bootstrapping**: 1,000 resamples to obtain a bootstrap CI for the interaction effect size.
- **Cross‑Validation**: 5‑fold CV reporting mean AUC and variance across folds.
- **Sensitivity Analysis**: Vary the adherence threshold (e.g., 3, 4, 5 weeks) and compute **p‑value stability** (standard deviation of the interaction p‑value across thresholds). This replaces the originally specified false‑positive‑rate metric, which is not computable without known ground truth.

### 4. Power & Sample‑Size Note
- No a priori power calculation is possible given the fixed dataset size; the analysis will explicitly acknowledge this limitation and report the achieved sample size (must meet SC‑001).

### 5. Reporting
All findings will be framed as **associational** (FR‑006). No causal language will be used.

## Kick‑back Note
The original specification mandates mixed‑effects and survival analyses, as well as a false‑positive‑rate sensitivity metric. Because the MyPersonality dataset is cross‑sectional and lacks weekly adherence data, the spec must be updated to reflect a cross‑sectional logistic regression approach and a p‑value‑stability sensitivity analysis.
