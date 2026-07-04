# Research: The Influence of Chatbot Politeness on User-Perceived Quality

## 1. Introduction & Hypothesis

**Research Question**: Does higher linguistic politeness in text-based chatbot responses lead to higher user-reported trust (perceived quality) in the chatbot?

**Hypothesis**: There is a positive **association** between the mean politeness score of chatbot utterances in a dialogue and the user's perceived quality rating of that dialogue, even after controlling for conversation length and user-specific effects.

**Statistical Framework**:
- **Outcome**: `quality_rating` (Ordinal, 1-5 Likert scale).
- **Primary Predictor**: `mean_politeness_score` (Continuous, z-scored).
- **Covariates**: `conversation_length` (Word count or utterance count), `age`, `gender` (if available).
- **Random Effects**: `user_id` (to account for repeated measures/non-independence).
- **Model**: Cumulative Link Mixed-Effects Model (CLMM).
- **Causal Framing**: This is an **observational study**. Claims will be framed as "associational". Causal influence is not claimed. Robustness to unmeasured confounding will be assessed via E-values.

## 2. Dataset Strategy

### Verified Datasets
The following datasets are verified and accessible. The plan strictly adheres to using only these sources.

| Dataset Name | Source URL (Verified) | Relevance | Variable Check |
|--------------|-----------------------|-----------|----------------|
| **HCI_P2** | ` | **Primary Source**. Contains dialogue data and explicit `quality_rating` (1-5) which serves as the proxy for trust. | **Critical Check**: Must verify `quality_rating` is ordinal 1-5 and chatbot text is present. |
| **EmpatheticDialogues** | ` | Secondary (Only if HCI_P2 lacks dialogue text). Contains emotion labels, **not** quality ratings. | **Excluded** for primary outcome due to missing `quality_rating`. |
| **Persona-Chat** | *No verified URL in block* | Spec mentions this dataset. | **Excluded** due to lack of verified URL and known lack of quality ratings. |

### Dataset Selection Rationale
1. **HCI_P2**: Selected as the **primary** dataset because it is the only verified source containing the required `quality_rating` (1-5) outcome variable. The analysis will proceed **only** if this variable is present and ordinal.
2. **EmpatheticDialogues**: Will **not** be used for the primary outcome. It may be used for supplementary politeness scoring if HCI_P2 lacks sufficient text, but the primary outcome must come from HCI_P2.
3. **Persona-Chat**: Excluded due to lack of verified URL and known absence of quality ratings.

**Variable Fit Confirmation (Pre-Implementation Check)**:
- **Required Variables**: `user_id`, `dialogue_id`, `quality_rating` (1-5), `text` (chatbot utterances), `age`, `gender`.
- **Gap Handling**: If `HCI_P2` lacks `age`/`gender`, subgroup analysis (FR-006) will be skipped for those variables. If it lacks `quality_rating`, the project will **abort** and flag a blocking data gap.

## 3. Statistical Methodology & Rigor

### 3.1 Primary Analysis (CLMM)
- **Model**: `quality_rating ~ politeness + conversation_length + (1 | user_id)`
- **Rationale**: The outcome is ordinal (1-5). Linear regression is inappropriate. CLMM handles the ordinal nature and the hierarchical structure (multiple dialogues per user).
- **Assumptions**:
 - **Proportional Odds**: The effect of politeness is constant across the thresholds of the outcome.
 - **Independence**: Residuals are independent given the random effects.
 - **Causal Claim**: **None**. This is an observational study. Claims will be framed as "associational".
 - **Confounding Control**: Potential confounders (length, demographics) are included as covariates. **E-values** will be calculated to quantify the robustness of the association to unmeasured confounding.

### 3.2 Multiple Comparison Correction
- **Method**: Benjamini-Hochberg (BH) procedure (preferred for power) or Bonferroni (conservative).
- **Application**: Applied to the p-values of fixed effects (politeness, length) across the primary model and robustness checks.
- **Rationale**: Controlling family-wise error rate (FR-004) when testing multiple hypotheses (main effect + covariates).

### 3.3 Power & Sample Size
- **Pre-Analysis**: A pilot run on [deferred] of the data will be performed to estimate effect size and calculate the **Minimum Detectable Effect (MDE)**. This justifies the sample size before full processing.
- **Acknowledgement**: The analysis will be reported with the caveat that it is an observational study.

### 3.4 Measurement Validity (Proxy Validation)
- **Politeness**: `jfiedler/politeness-bert` is a BERT-based model trained on the Politeness Corpus. It is a standard, validated tool for this task.
- **Trust/Quality**: The `quality_rating` (1-5) is used as a proxy. The plan mandates **citing a specific HCI literature source** that validates the use of this specific rating in HCI_P2 as a proxy for "trust". If no such source exists, the limitation will be explicitly stated in the final report.

### 3.5 Collinearity Diagnosis
- **Method**: Variance Inflation Factor (VIF) for fixed effects.
- **Threshold**: VIF < 5.
- **Action**: If `politeness` and `conversation_length` are highly collinear (VIF ≥ 5), the plan will re-fit the model without the collinear covariate or report the correlation descriptively, acknowledging that independent effects cannot be claimed.

## 4. Robustness & Subgroup Analysis

### 4.1 Alternative Classifier (Open-Source)
- **Method**: Re-compute politeness scores using the `textstat` library (using `bing` or `afinn` lexicons) and the `politeness` package.
- **Comparison**: Correlation of **predicted quality scores** between BERT and lexicon models (SC-004).
- **Rationale**: Ensures findings are not an artifact of the specific BERT model. **LIWC-2015 is not used** due to licensing; open-source alternatives are the standard.

### 4.2 Subgroup Analysis
- **Variables**: Age, Gender.
- **Condition**: n ≥ 30 per subgroup (FR-006).
- **Method**: Fit separate CLMMs or interaction terms (`politeness * age_group`).
- **Correction**: Apply multiplicity correction for subgroup tests.

## 5. Computational Feasibility

- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - **R Installation**: CI workflow will install `r-base` and `lme4` to support `rpy2`.
 - **Batch Processing**: Process dialogues in batches for BERT inference to avoid OOM.
 - **Data Subsetting**: If dataset > 10k dialogues, sample 10k randomly for the primary run, or process in chunks.
 - **Model Loading**: Load `politeness-bert` once and reuse; avoid reloading per utterance.
 - **CLMM**: Use `rpy2` to call R's `lme4` (preferred) or `statsmodels` (fallback) with optimized solvers.
 - **Convergence Fallback**: If CLMM fails, switch to fixed-effects ordinal regression.

## 6. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use HCI_P2 as Primary** | Only verified dataset with required `quality_rating` (1-5) outcome. |
| **Use CLMM over GLM** | Outcome is ordinal (1-5); GLM assumes continuous. |
| **Use Benjamini-Hochberg** | More powerful than Bonferroni for multiple tests while controlling FDR. |
| **Subgroup n ≥ 30** | Ensures statistical validity; prevents overfitting on small groups. |
| **Fallback to Fixed Effects** | If CLMM fails to converge, a simpler model is preferred over no result. |
| **Open-Source Lexicon** | `textstat`/`politeness` used instead of proprietary LIWC to ensure reproducibility. |
| **E-Value Calculation** | Required to assess robustness to unmeasured confounding in observational design. |
