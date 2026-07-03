# Research: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## Summary
This research plan outlines the methodology for testing whether perspective-taking instructions reduce moral outrage in online discourse. It details the data sources, experimental design, statistical analysis plan, and computational constraints.

## Dataset Strategy

### Stimulus Data: "Against the Others!"
- **Source**: "Against the Others!" Twitter dataset.
- **Access**: The plan requires a **verified, canonical URL** (e.g., OSF, HuggingFace, or GitHub Release) to be identified during the "Verified Accuracy" gate. The pipeline will fail with a clear error if the file `data/raw/twitter_posts.parquet` is missing or if the URL cannot be reached, ensuring reproducibility (Constitution Principle I).
- **Content**: Twitter posts on controversial topics (climate, immigration).
- **Usage**: Ingested to create the stimulus pool.
- **Variable Fit**: Contains text and topic metadata required for filtering and stratification.

### Sentiment Reference: VADER Algorithm
- **Source**: VADER (Valence Aware Dictionary and sEntiment Reasoner) algorithm (Hutto & Gilbert).
- **Implementation**: Python library `vaderSentiment`.
- **Usage**: Computed programmatically for each post to stratify the stimulus pool into "Moderate" and "High" intensity bins.
- **Note**: VADER measures general sentiment, not specifically "moral outrage." This is acknowledged as an approximate proxy for intensity stratification.

### Participant Data
- **Source**: Raw CSV uploads from experimental participants.
- **Content**: Responses to 7-item Moral Outrage Scale, attention checks, demographics, and **a `consent_given` flag**.
- **Access**: `data/raw/participant_responses.csv`.

## Experimental Design

### Hypothesis
H: Participants in the perspective-taking condition will report significantly lower mean moral outrage scores than those in the control condition.

### Design Type
Between-subjects randomized controlled trial (RCT).
- **Condition A (Perspective-Taking)**: "Explain why the author might hold this view."
- **Condition B (Control)**: "Summarize the post in one sentence."

### Randomization & Stratification
1. **Filter**: Select posts on climate/immigration.
2. **Stratify**: Compute VADER sentiment for each post. Bin into "Moderate" and "High" intensity.
3. **Stratified Randomization**: Randomly select 30 posts from "Moderate" and 30 from "High" (Total N=60). **Within each intensity bin**, posts are randomly assigned to the perspective-taking or control condition to ensure balance of intensity across conditions.
4. **Assign**: For each post, generate two instruction versions. Participants are randomly assigned to one condition.

### Sample Size & Power
- **Target**: 240 participants (120 per condition).
- **Power Calculation**: Based on an independent t-test, α=0.05, Power=0.80, Effect Size (d)=0.5.
- **Assumption**: This sample size is sufficient to detect a medium effect. If the actual effect size is smaller, the study may be underpowered (acknowledged limitation).

## Statistical Analysis Plan

### Primary Analysis Decision Tree
1. **Calculate ICC**: Compute Intra-Class Correlation (ICC) on the **raw, unaggregated** data (5 posts per participant) to assess clustering.
2. **Decision Rule**:
   - **If ICC < 0.05**: Proceed with **Independent-Samples t-test** on mean outrage scores.
   - **If ICC >= 0.05**: **Switch to Linear Mixed-Effects (LME) Model** with random intercepts for participants to account for clustering. The t-test is considered invalid in this case due to pseudoreplication.
3. **Model Specification (LME)**: `outrage_score ~ condition + intensity_bin + (1 | participant_id)`.
   - **Fixed Effects**: `condition` (Perspective-Taking vs. Control), `intensity_bin` (Moderate vs. High).
   - **Random Effects**: Random intercept for `participant_id`.

### Metrics
- **t-test**: t-statistic, p-value, Cohen's d, 95% Confidence Interval.
- **LME**: Fixed effect coefficient for `condition`, standard error, p-value (via Satterthwaite approximation), 95% CI.
- **Robustness**: Mann-Whitney U test (if t-test path) or robustness check for LME.

### Secondary Analysis (Validity)
- **Attention Checks**: Participants failing >1 check, exhibiting zero variance (straight-lining), or **lacking `consent_given == true`** are excluded (FR-003).
- **Integrity**: Report ICC value and the analysis path chosen (t-test vs. LME).

### Framing
- **Causal**: Due to randomization (stratified by intensity), findings are framed as the causal effect of the intervention.
- **Associational**: If randomization fails (checked via baseline balance), findings are framed as associational.

## Computational Constraints
- **Hardware**: Free-tier CI (2 CPU, 7 GB RAM).
- **Libraries**: `pandas`, `scipy`, `statsmodels`, `vaderSentiment`.
- **Exclusions**: No GPU, no deep learning, no large LLM inference.
- **Runtime**: Target <10 minutes.

## Risks & Mitigations
- **Dataset Insufficiency**: If <60 posts available after filtering, halt with `DATASET_INSUFFICIENT` error (FR-008).
- **Low Power**: If N < 240, report power limitation and interpret results cautiously.
- **VADER Validity**: Acknowledge VADER as an approximation of outrage intensity; report this limitation in the discussion.
- **Clustering**: If ICC is high, the t-test is invalid; the plan mandates LME to correct for this.