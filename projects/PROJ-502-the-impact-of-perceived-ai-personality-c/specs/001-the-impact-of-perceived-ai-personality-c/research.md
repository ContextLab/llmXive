# Research: The Impact of Perceived AI Personality Consistency on User Trust (Revised Scope)

## Overview

**Original Hypothesis**: Perceived AI personality consistency predicts user trust.
**Revised Hypothesis**: **Textual Variance** (sentiment and lexical diversity) within a conversation session predicts **Session Engagement** (interaction length) in the DailyDialog dataset.

**Critical Limitation**: The DailyDialog dataset is a static snapshot of human-human dialogues. It lacks:
1. **User IDs**: No way to link multiple sessions to the same user.
2. **Timestamps**: No way to calculate "time between sessions" or "time-to-event".
3. **AI Traits**: No way to measure "AI personality" or "trust" in an AI context.

Therefore, this study **cannot** test the original hypothesis. It is re-scoped to analyze **within-session dynamics** in human dialogue as a proxy for engagement patterns. All claims regarding "AI" or "Trust" are explicitly removed from the analysis and framed as limitations. The "Proxy Validity Analysis" (KS test) has been removed as no valid reference dataset exists.

**Study Design**: Cross-sectional, observational analysis of conversation logs using Turn-Level Lag (Predictor: Turns 1 to N-1; Outcome: Turn N).

## Dataset Strategy

We utilize the **DailyDialog** dataset. The previous plan to use an "AI-Human reference dataset" for validity checking has been removed because no such dataset exists with the required longitudinal metrics.

| Dataset Role | Source Name | Verified URL | Rationale |
|:--- |:--- |:--- |:--- |
| **Primary Data** | DailyDialog | ` | Rich, multi-turn dialogue data. Selected for its structured turn format and availability of `parquet` for efficient CPU loading. |
| **Domain Shift** | None | N/A | The previous AI-Human reference dataset was removed. The study acknowledges the domain gap (Human-Human vs. AI-Human) as a limitation and does not attempt to quantify it via a KS test. |

## Methodology & Statistical Plan

### 1. Data Ingestion & Filtering (FR-001)
- **Source**: DailyDialog `parquet`.
- **Filter**: Retain only sessions with **≥3 turns**.
- **Validation**: Checksum verification; PII scan (regex-based for emails/phones).
- **Note**: No Proxy Validity Analysis (KS test) is performed due to lack of reference data.

### 2. Metric Computation (Turn-Level Lag)
To minimize circularity within a single session:
- **Predictor (Variance)**: Computed from **Turns 1 to N-1**.
 - **Sentiment Variance**: Variance of sentiment scores across Turns 1 to N-1.
 - **Lexical Diversity Variance**: Variance of Type-Token Ratio (TTR) across Turns 1 to N-1.
 - **Composite**: `Variance_Score = 1 - (z_sentiment_var + z_ttr_var) / 2`.
- **Outcome (Engagement)**: Computed from **Turn N** (the final turn or a specific target turn).
 - **Interaction Length**: Word count of Turn N.
 - **Session Length**: Total word count of the session (as a control).
- **Robustness**:
 - Handle zero variance by setting score to 0.
 - Skip responses with sentiment model errors.
 - **Dynamic Batching**: Calculate max batch size based on 7GB RAM limit.

### 3. Statistical Analysis
- **Model 1: GLM (Count Data)**
 - **Outcome**: Interaction Length (word count of Turn N).
 - **Family**: Negative Binomial (if overdispersion detected) or Poisson.
 - **Predictors**: Variance Score.
 - **Controls**: Total session length, number of turns.
- **Model 2: Linear Regression**
 - **Outcome**: Turn N word count.
 - **Predictors**: Variance Score.
 - **Controls**: Session length, turn count.
- **Multiple Comparison Correction**:
 - Apply Benjamini-Hochberg (FDR) correction if multiple hypotheses are tested.
- **Power Analysis**:
 - **Pre-study**: Estimate sample size (N) from DailyDialog.
 - **Calculation**: Calculate power to detect r=0.3 with N=sessions.
 - **Reporting**: If power < 0.8, report effect sizes with confidence intervals and explicitly state the power limitation.

### 4. Visualization (FR-006)
- **Scatter Plot**: Variance Score (X) vs. Turn N Length (Y) with regression line.
- **Histogram**: Distribution of Variance Scores.
- **Format**: PNG, high resolution, saved to `output/figures`.

## Decision Rationale & Feasibility

- **CPU-Only Constraint**: The plan avoids GPU-intensive models. `distilbert-base-uncased` is small enough for CPU inference with batch processing.
- **Memory Management**: Dynamic batching ensures the process never exceeds 7GB RAM.
- **Dataset Fit**: DailyDialog provides sufficient turns (≥3) for variance calculation. The study is re-scoped to **within-session** analysis only.
- **Statistical Rigor**:
 - **Causal Claims**: None. All findings framed as associational.
 - **Collinearity**: Variance and length may be correlated; VIF will be checked.
 - **Measurement Validity**: Variance is a statistical proxy for "variability," not "personality." This is explicitly acknowledged as a limitation.
 - **Removed Validity Check**: The Proxy Validity Analysis (KS test) was removed as no valid AI-human reference dataset exists. The study proceeds with the explicit acknowledgment that human-human dynamics are a proxy for engagement, not a validated measure of AI trust.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **DailyDialog lacks AI characteristics** | High (Invalid proxy) | **Reframed**: The study no longer claims to measure AI personality. It measures "Textual Variance" in human dialogue. |
| **Sentiment model fails on dialect/slang** | Medium (Noisy metrics) | Fallback model configured via env var. Error logging. |
| **OOM on Free Tier** | Critical (Job failure) | Dynamic batching and subset sampling if necessary. |
| **Low Power (Small N)** | Medium (Type II error) | Pre-study power analysis; report effect sizes with confidence intervals. |
| **Circularity** | High (Spurious correlation) | **Mitigated**: Used Turn-Level Lag (Turns 1 to N-1 for predictor, Turn N for outcome) to separate predictor and outcome text. |
| **Removed Proxy Validity** | Medium (Unquantified gap) | **Mitigated**: Explicitly state in limitations that the domain gap (Human-Human vs. AI-Human) is unquantified and findings are limited to human dialogue dynamics. |