# Research: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Overview

This research plan addresses the core question: Do subtle variations in linguistic style—such as first-person pronoun frequency, hedging language, and emotional valence—predict human ratings of perceived authenticity in AI chatbot conversations? The study is observational; all findings will be framed as associational.

## Dataset Strategy

### Verified Datasets

Only the following dataset has been verified for reachability and format compatibility:

- **Dataset**: MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score  
  **URL**: https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet  
  **Loader**: `datasets.load_dataset("parquet", data_files="...")`  
  **Content**: Text-only responses from LLaMA-3.2 model; contains conversational turns suitable for linguistic feature extraction.  
  **Limitation**: Does **not** contain human-rated authenticity scores.

### Gap Identification & Resolution Strategy

**Fatal Mismatch**: The spec requires **human authenticity ratings** (FR-009, US-2) to correlate with linguistic features. The verified dataset (`MixSub-LLaMA-3.2`) provides **text only** and lacks any authenticity labels.

**Resolution Strategy**:
1. **Primary Path (Annotation)**: Since no verified dataset with human ratings exists, the project will execute **Phase 0: Data Acquisition & Annotation**. This involves:
   - Selecting a random sample of ≤10,000 conversations from the verified text dataset.
   - Recruiting human annotators to rate authenticity on a -5 Likert scale.
   - Calculating Krippendorff's alpha (target ≥ 0.7) to ensure inter-rater reliability (FR-009, SC-006).
   - Generating a `ratings.csv` file linked to `conversation_id`.
2. **Secondary Path (New Source)**: If annotation is infeasible, the project will search for a new verified dataset containing both text and human authenticity ratings. If found, it will replace the current dataset.
3. **Blocking Condition**: The statistical analysis pipeline (correlation/regression) **cannot proceed** until a verified `ratings.csv` is generated or sourced. The plan explicitly halts at Phase 0 if this condition is not met.

> **Note**: The plan does **not** invent or guess a dataset URL. The gap is explicitly documented to prevent fatal dataset-variable mismatch.

## Methodological Rigor

### Theoretical Justification

The plan hypothesizes that specific linguistic cues signal authenticity:
- **Hedging**: May signal intellectual honesty, appropriate uncertainty, and humility, which are traits associated with perceived authenticity.
- **First-Person Pronouns**: May signal personal ownership and engagement, potentially increasing perceived authenticity.
- **Emotional Valence**: Moderate positive valence may signal warmth and genuineness, while extreme valence may signal manipulation.
*Note: This is an associational hypothesis. The plan explicitly avoids causal claims.*

### Statistical Approach

1. **Feature Extraction** (FR-001, US-1):  
   - **Pronoun Rate**: Count of first-person pronouns (`I`, `me`, `my`, `mine`, `we`, `us`, `our`, `ours`) divided by total word count (using `spaCy` `en_core_web_sm`).  
   - **Hedge Density**: Count of hedge words (`maybe`, `perhaps`, `possibly`, `probably`, `likely`, `might`, `could`, `would`) divided by total word count (using NLTK tokenization + predefined lexicon).  
   - **Valence Score**: VADER composite sentiment score (-1.0 to 1.0) per conversation.  
   - **Controls**: Conversation length (word count), turn count (number of speaker turns).

2. **Correlation Analysis** (FR-002, US-2):  
   - Compute Pearson and Spearman correlations between each linguistic feature and authenticity score.  
   - Apply Benjamini-Hochberg correction (alpha = 0.05) for multiple comparisons (SC-004).  
   - Report p-values, effect sizes, and confidence intervals.

3. **Multivariate Regression** (FR-003, US-3):  
   - Fit multiple linear regression: `authenticity ~ pronoun_rate + hedge_density + valence_score + log(length) + turn_count`.  
   - Report adjusted R², AIC, coefficients, standard errors, p-values.  
   - Test for non-linearity (FR-010) via quadratic terms or splines; if significant, report non-linear model.  
   - Compute Variance Inflation Factors (VIF) for all predictors; flag if VIF > 5 (SC-003).

4. **Diagnostic Checks** (FR-008, Edge Cases):  
   - Shapiro-Wilk test for normality; flag skewed distributions (p < 0.05).  
   - Handle empty/short texts (<5 words) by skipping metric calculation and logging.  
   - Exclude rows with missing ratings; log count.

### Causal Inference Assumptions

- **Observational Design**: No randomization; all claims strictly associational.  
- **No Causal Language**: Output must include: "These results indicate association, not causation." (FR-004).  
- **Confounding**: Controlled via regression (length, turn count); acknowledge unmeasured confounders.

### Measurement Validity

- **Authenticity Scale**: Must be 1-5 Likert scale (FR-009); inter-rater reliability (Krippendorff’s α ≥ 0.7) required if human annotation is performed.  
- **Linguistic Tools**: `spaCy` (v3.5), `NLTK` (v3.8), `VADER` (v3.3.2) are standard, validated tools for these metrics.

### Power & Sample Size

- **Assumption**: Sample ≤10,000 conversations (Assumptions section).  
- **Power Justification**: For a two-tailed correlation test at alpha=0.05, N=10,000 provides >99% power to detect a small effect size (Cohen's r ≥ 0.04-0.05).  
- **Limitation**: Detecting very small effects (r < 0.04) would require a larger sample (N > 150,000). The study acknowledges a potential Type II error risk for effects smaller than r=0.04.  
- **Mitigation**: Report effect sizes and confidence intervals; avoid overinterpretation of non-significant results.

### Multiple Comparisons

- **Correction**: Benjamini-Hochberg (alpha = 0.05) applied to family of 3 correlation tests (SC-004).  
- **Rationale**: Controls false discovery rate while maintaining power.

### Collinearity

- **Risk**: Text length and feature density may be correlated (e.g., longer texts may have more pronouns).  
- **Mitigation**:  
  - Normalize features per word count.  
  - Compute VIF; if >5, report collinearity and consider dimension reduction or descriptive reporting only.  
  - Do **not** claim independent effects if predictors are definitionally related.

## Decision Rationale

- **CPU-Only Methods**: All libraries (`spaCy`, `NLTK`, `VADER`, `scikit-learn`, `statsmodels`) have CPU wheels and run within 7 GB RAM for ≤10,000 rows.  
- **Sampling**: If source dataset >10,000 rows, random sample drawn to fit CI constraints (SC-005).  
- **Non-Linearity Test**: Included per FR-010; if quadratic term significant, report non-linear model.  
- **Gap Handling**: Dataset lacking authenticity scores is explicitly flagged; no workaround invented. The plan mandates a manual annotation protocol or new data source to resolve the gap.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| No verified dataset with human authenticity ratings | Flag gap; execute Phase 0 (manual annotation) or source new dataset. |
| Skewed feature distributions | Log-transform or use non-parametric methods; flag in report. |
| Multicollinearity (VIF >5) | Report VIF; avoid claiming independent effects; use descriptive stats. |
| Small sample size (underpowered for r < 0.04) | Report effect sizes; acknowledge limitation; avoid overinterpretation. |
| Missing ratings | Exclude rows; log count. |
| Empty/short texts | Skip calculation; log exclusion. |