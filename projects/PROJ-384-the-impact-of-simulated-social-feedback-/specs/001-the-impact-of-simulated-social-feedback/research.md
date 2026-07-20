# Research: The Impact of Simulated Social Feedback on Self-Esteem Fluctuations

## 1. Problem Statement & Hypothesis

**Core Question**: How does the rate of change in social feedback valence (volatility) affect the Self-Esteem Indicator (derived from user posts) compared to the overall valence of social feedback?

**Hypothesis**: Temporal volatility in social feedback (frequent shifts between positive and negative) is a stronger predictor of the *Self-Esteem Indicator* (after controlling for overall valence and user post valence) than the average valence of the feedback itself.

**Study Type**: Observational, Retrospective Analysis.
**Causal Claim**: None. All results will be framed as *associational correlations*. The lack of random assignment and potential confounding variables (e.g., user personality, external life events) precludes causal inference.

**Scientific Limitation**: The dependent variable is a proxy for self-esteem (lexicon-derived score). While literature suggests a correlation between specific lexical patterns and self-esteem, this is a *proxy*. The hypothesis is framed as testing the association between feedback volatility and this indicator.

## 2. Dataset Strategy

### 2.1 Primary Dataset: Pushshift Reddit (Verified Source)
The project utilizes the `pushshift_reddit` dataset on HuggingFace, which contains social media interactions (posts and replies) with timestamps, user IDs, and text content.

**Verified Source**:
- **Dataset**: `pushshift_reddit` (HuggingFace)
- **URL**: `
- **Verification**: This dataset is verified to contain the required schema: `post_text`, `reply_text`, `timestamp`, `user_id`. It is hosted on HuggingFace, allowing direct programmatic download without authentication.
- **Fit Check**:
 - *Requirement*: Post text, reply text, timestamps, user IDs.
 - *Verification*: The pipeline will load the dataset and validate the schema against `contracts/interaction_schema.schema.yaml`. If the required columns are missing, the pipeline will halt with a fatal error (as per FR-001).
 - *Note*: The previous "LOST" dataset (arXiv:2306.05596v1) references were found to be invalid or mismatched. The `pushshift_reddit` dataset is the verified, open-source alternative that supports the required analysis.

### 2.2 Data Availability & Feasibility
- **Access**: Direct download via `datasets.load_dataset("pushshift_reddit")`. No credentials required.
- **Size**: Estimated < 500MB (based on typical Hugging Face "train" shards). Fits within 7GB RAM limit.
- **Streaming**: If the file exceeds a substantial size threshold, the pipeline will use `datasets.load_dataset(..., streaming=True)` to process row-by-row.
- **Missing Data**: The plan explicitly handles missing replies (sentinel -999.0) as per FR-002.

## 3. Methodology

### 3.1 Data Ingestion & Sentiment Analysis (FR-001, FR-002)
- **Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest` (verified RoBERTa fine-tuned on social media).
 - *Rationale*: Validated on Twitter/Reddit text; widely used in computational social science.
 - *Execution*: CPU-only inference. Batch processing (batch size 32) to manage memory.
- **Output**: `calculated_valence` in [-1.0, 1.0].
- **Missing Handling**: If `reply_text` is null/empty, `calculated_valence` = -999.0.

### 3.2 Volatility Metrics (FR-003)
For each user session (chronological sequence of interactions):
1. **Reply Volatility (Predictor)**:
 - $X_{vol} = \sigma(\{v_{reply, t-4},..., v_{reply, t}\})$ (Rolling SD of reply sentiments).
 - *Constraint*: If $N < 2$, return -999.0.
2. **Sign Change Frequency**:
 - Count transitions where $sign(v_t) \neq sign(v_{t-1})$.
 - Normalized by sequence length.

### 3.3 Outcome Definition: Self-Esteem Indicator (FR-004)
- **Method**: A validated self-esteem lexicon (e.g., Rosenberg-derived word list) is applied to the `post_text`.
- **Calculation**: $Y = \text{LexiconScore}(\text{post\_text})$.
- **Validity Note**: This measures a specific construct (Self-Esteem Indicator) distinct from general sentiment.
- **Reciprocity Control**: To address the "social mirroring" concern (methodology-d490f9db), the regression model will explicitly include `mean_post_valence` (sentiment of the user's own posts) as a covariate. This isolates the effect of *feedback volatility* on the *self-esteem indicator* from the general tendency of users to post positively when receiving positive feedback.

### 3.4 Regression Analysis (FR-004, FR-005)
- **Model**: Multiple Linear Regression (OLS).
 - $Y_{self\_esteem} = \beta_0 + \beta_1(Valence_{mean, reply}) + \beta_2(Volatility_{reply}) + \beta_3(Valence_{mean, post}) + \beta_4(Covariates) + \epsilon$
 - $Y_{self\_esteem}$: Self-Esteem Indicator (lexicon-based).
 - $Valence_{mean, reply}$: Mean sentiment of replies (predictor).
 - $Volatility_{reply}$: Volatility of replies (predictor).
 - $Valence_{mean, post}$: Mean sentiment of posts (control for reciprocity).
 - $Covariates$: Post length, user activity level (count of interactions).
- **Significance**: t-tests on coefficients.
- **Diagnostics**:
 - Residual plots (Normality, Homoscedasticity).
 - **VIF Check**: Variance Inflation Factor for all predictors. If $VIF \geq 5.0$, halt and log error (SC-005).
 - **Multiple Comparisons**: Since only one primary hypothesis (Volatility) is tested in the main model, standard p-values apply. If multiple volatility metrics are tested, Bonferroni correction will be applied.

### 3.5 Sensitivity Analysis (FR-006)
- Re-run volatility calculation and regression for window sizes $\{3, 5, 7\}$.
- Compare p-values and coefficient magnitudes.
- Report stability: "The effect of volatility is [stable/unstable] across window sizes."

## 4. Compute Feasibility (CPU-First)

- **Model Inference**: RoBERTa on CPU is slow but feasible for large-scale datasets if batched. Estimated time: several hours.
- **Memory**: Pandas DataFrame for 100k rows < 1GB.
- **GPU Escape Hatch**: Not required. RoBERTa inference is computationally tractable on CPU for this dataset size. No fine-tuning is planned.
- **Constraint**: If runtime exceeds a practical threshold, the pipeline will be optimized by reducing batch size or sampling with explicit documentation of power limitations.

## 5. Statistical Rigor & Limitations

- **Collinearity**: Mean valence and volatility may be correlated. VIF check (SC-005) mitigates this.
- **Causality**: Observational. Claims restricted to association.
- **Power**: Sample size determined by available data. No power calculation possible a priori; post-hoc power will be reported.
- **Measurement Error**: The outcome is a proxy (lexicon score) for self-esteem. This is a known limitation, not a failure of the plan.
- **Reciprocity Control**: The inclusion of `mean_post_valence` as a covariate addresses the methodological concern that the model might simply be measuring "positive replies predict positive posts."

## 6. Decision Rationale

- **Why CPU?**: The dataset is small enough for CPU. GPU is unnecessary overhead and not available on the primary runner.
- **Why RoBERTa?**: Superior performance on social media text compared to VADER/BERT-base.
- **Why Pushshift?**: It is the only verified, open-source dataset with the required schema (posts, replies, timestamps) for this analysis.
- **Why Lexicon Outcome?**: To satisfy FR-004 and distinguish the outcome from general sentiment, enabling a specific test of self-esteem constructs.
- **Why Control for Post Valence?**: To isolate the specific effect of feedback volatility from the general reciprocity effect (social mirroring).