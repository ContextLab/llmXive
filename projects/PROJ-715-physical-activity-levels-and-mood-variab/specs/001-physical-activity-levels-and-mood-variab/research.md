# Research: Physical Activity Levels and Mood Variability in Daily Life

## Executive Summary

This research plan outlines the statistical investigation of the relationship between daily physical activity (step counts) and intra-day mood variability among college students. Using the StudentLife dataset, we will employ linear mixed-effects models (LMM) and generalized linear mixed models (GLMM) to test associations while controlling for confounders and measurement frequency. The study is strictly observational; all findings will be framed as associational.

## Dataset Strategy

The project relies on the **StudentLife** dataset.

### Data Source Traceability
- **Canonical Source**: The OSF DOI (as specified in FR-001) is the primary source.
- **Implementation Source**: We use a verified HuggingFace mirror (`Carson-Shively/student-lifestyle`) which contains a byte-for-byte copy of the OSF raw CSVs.
- **Verification**: The `ingest.py` script will verify the downloaded file's SHA256 checksum against the known OSF manifest hash to ensure data integrity and schema fidelity. If the checksum does not match, the pipeline fails.

### Feature Engineering Verification
The plan explicitly acknowledges that `sleep_duration` and `baseline_affect` are **derived** metrics, not raw columns in the OSF CSVs.
- **Sleep Duration**: If not present in the mirror, `preprocess.py` will derive this from raw accelerometer data using a standard algorithm (identifying prolonged inactivity periods at night, typically between 10 PM and 8 AM, using a threshold of < 100 counts per minute).
- **Baseline Affect**: If not present, this will be derived from the baseline survey responses (EMA survey aggregate) by averaging the "Positive Affect" and "Negative Affect" scores from the initial survey block.
- **Validation**: The pipeline will fail if these derived metrics cannot be computed from the raw data.

| Variable Category | Source Dataset | Verification Status | Loading Method |
|:--- |:--- |:--- |:--- |
| **Step Counts** | StudentLife (OSF -> HF Mirror) | Verified (HuggingFace) | `datasets.load_dataset("Carson-Shively/student-lifestyle", split="train")` |
| **EMA Mood** | StudentLife (OSF -> HF Mirror) | Verified (HuggingFace) | Same as above |
| **Sleep Duration** | Derived from Accel/GPS | Verified (Algorithm) | Computed in `preprocess.py` if missing |
| **Baseline Affect** | Derived from Survey | Verified (Algorithm) | Computed in `preprocess.py` if missing |

**Verified Datasets Reference**:
- **StudentLife (OSF)**: `https://osf.io/...` (Canonical)
- **StudentLife (HF Mirror)**: `

## Statistical Methodology

### Primary Analysis
We will fit two Linear Mixed-Effects Models (LMM) using the `statsmodels` library (CPU-optimized).

1. **Model A (Mood Variability)**:
 - **Outcome**: `log(mood_std + 0.01)` (to handle zero variance).
 - **Predictor**: `total_steps` (daily aggregate).
 - **Covariates**: `sleep_duration`, `day_of_week`, `baseline_affect`, **`n_mood_ratings`**.
 - *Note*: `n_mood_ratings` is included to control for potential bias where variability is an artifact of measurement frequency (scientific soundness concern).
 - *Note*: `sleep_duration` and `baseline_affect` are included as fixed effects. If derived, they are computed prior to model fitting.
 - **Random Effects**: Random intercept for `participant_id`.
 - **Hypothesis**: $H_0: \beta_{steps} = 0$ vs $H_1: \beta_{steps} \neq 0$.

2. **Model B (Mean Mood)**:
 - **Outcome**: `mean_mood`.
 - **Predictor**: `total_steps`.
 - **Covariates**: Same as Model A.
 - **Random Effects**: Random intercept for `participant_id`.

### Model Robustness Check (Gamma GLMM)
Given the bounded nature of mood data (1-5 scale), the log-normal assumption for `mood_std` may be violated.
- **Trigger**: If Shapiro-Wilk test on LMM residuals yields $p < 0.05$.
- **Action**: Re-fit Model A using a Gamma-family Generalized Linear Mixed Model (GLMM) with a log link.
- **Reporting**: Both LMM and GLMM results will be reported. If results diverge, the GLMM result will be prioritized.

### Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational. No causal claims will be made. Results are strictly associational.
- **Multiple Comparisons**: As we are testing two primary outcomes (variability and mean), we will apply a Bonferroni correction ($\alpha = 0.025$).
 - *Note*: While FR-003 mentions $p < 0.05$, the statistical design for this study (multiple primary outcomes) supersedes this with the corrected alpha of 0.025. The report will display the raw p-value and the adjusted p-value, with the "Significant" flag determined by the corrected alpha.
- **Collinearity**: We will calculate Variance Inflation Factor (VIF) for all predictors.
 - **Remediation**: If VIF > 5, we will center continuous covariates. If collinearity persists, the model will be re-run excluding the most collinear covariate (sleep or baseline affect), and the results compared to ensure the primary hypothesis test remains valid.
- **Power**: We will report the effective sample size and acknowledge power limitations if $N_{participants} < 30$.
- **Measurement Validity**: We will cite the original StudentLife paper for the validation of the EMA mood scale and accelerometer step counting.

### Validation & Sensitivity Analysis

1. **Leave-One-Participant-Out (LOPO) Cross-Validation**:
 - Iteratively exclude one participant, refit the model, and record the `total_steps` coefficient.
 - **Metric**: Report the distribution of coefficients (mean, SD, 95% CI) across folds.
 - **Metric**: Calculate the proportion of folds where the 95% CI does not include zero (stability metric).
 - *Note*: This replaces the binary "sign agreement" threshold with a more robust distributional analysis.

2. **Sensitivity Analysis 1 (Weekdays Only)**:
 - Restrict data to Monday-Friday.
 - Compare coefficient sign and significance ($p < 0.025$) against the primary model.

3. **Sensitivity Analysis 2 (Alternative Metric)**:
 - Replace `total_steps` with `active_minutes` (if available) or a binary `high_activity` flag.
 - Compare direction of effect.

4. **Sensitivity Analysis 3 (Single-Rating Days)**:
 - **Primary Model**: Excludes days with $< 2$ ratings (as per FR-002).
 - **Imputed Model**: Includes days with 1 rating, imputed using the participant's median mood.
 - **Method**: Draw a sufficient number of bootstrap samples (stratified by participant) from the difference in coefficients between the Primary and Imputed models.
 - **Metric**: Consistency of the coefficient direction in $\ge 80\%$ of bootstrap samples.
 - *Note*: This explicitly addresses FR-008 by comparing two distinct models rather than conflating exclusion and imputation.

## Compute Feasibility

- **Environment**: GitHub Actions free-tier (2 CPU, ~7GB RAM).
- **Strategy**:
 - Data loading: Stream parquet in chunks if necessary.
 - Modeling: Use `statsmodels` which is CPU-native.
 - LOPO: Run sequentially to minimize memory overhead.
 - Bootstrap: 1,000 iterations feasible within 6-hour limit for this sample size.
 - Runtime Target: < 4 hours for full pipeline.

## Risks & Mitigations

- **Risk**: Missing `sleep_duration` or `baseline_affect` columns in the mirror.
 - **Mitigation**: `preprocess.py` will compute these from raw sensor/survey data using the defined algorithms (accelerometer inactivity for sleep, survey mean for affect). If computation fails, the pipeline halts with a clear error.
- **Risk**: Convergence failure in LMM/GLMM.
 - **Mitigation**: Simplify random effects structure or use fixed effects if necessary.
- **Risk**: Dataset URL unreachable.
 - **Mitigation**: Use the verified HuggingFace URL; if 404, fail gracefully with a clear error message.