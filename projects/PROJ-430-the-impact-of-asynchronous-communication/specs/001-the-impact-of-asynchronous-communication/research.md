# Research: Asynchronous Communication Delays and Team Cohesion

## Research Question
**Is there an association** between response-time variability in asynchronous communication channels and perceived team cohesion in distributed software teams?
*(Note: The study is strictly associational due to the cross-sectional, observational nature of the data. No causal claims regarding "influence" or directionality are made.)*

## Theoretical Background
Asynchronous communication introduces latency, which can lead to ambiguity and reduced social presence. In distributed teams, high variance in response times may signal unreliability or lack of engagement, potentially eroding trust. Conversely, consistent (even if slow) response patterns might foster stability. This study tests the hypothesis that higher response-time variance is **associated** with lower cohesion scores.

**Methodological Correction**: To avoid ecological fallacy, the primary analysis operates at the **Contributor Pair level**, modeling the relationship between a specific pair's delay variance and their specific interaction sentiment, while accounting for project-level clustering.

## Dataset Strategy

### Primary Data Source: GitHub API
The study relies on public GitHub repository metadata. The GitHub API provides programmatic access to issues, pull requests, and comments, including timestamps and author information.
- **Access Method**: Direct API calls via `requests` library with pagination and rate-limit handling.
- **Feasibility**: Public data is freely accessible without credentials (within rate limits).
- **Variables Extracted**: `created_at`, `author`, `body` (text), `type` (issue/PR/comment), `in_reply_to_id` (for thread context).

### Secondary Data Source: VADER Sentiment Model
For the cohesion proxy, we use the VADER (Valence Aware Dictionary and sEntiment Reasoner) lexicon, a rule-based algorithm for social media text.
- **Source**: PyPI Package (`vaderSentiment`) and Original Academic Paper (Hutto & Gilbert, 2014).
- **URLs**:
 - `https://pypi.org/project/vaderSentiment/`
 - Hutto, C. J., & Gilbert, E. E. (n.d.). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. *ICWSM*.
- **Rationale**: VADER is specifically tuned for social media and short text, making it suitable for GitHub comments. It is CPU-tractable and does not require GPU resources.

### # Verified datasets
- **GitHub API**: ` Name or service not known)"))] (Verified: Public, Programmatic Access).
- **VADER Model**: `https://pypi.org/project/vaderSentiment/` (Verified: PyPI, Stable).

### Dataset Variable Fit
- **Predictors**: `response_time_variance`, `mean_delay` (derived from GitHub timestamps at pair level).
- **Outcome**: `cohesion_proxy_score` (derived from VADER sentiment on GitHub comments at pair level).
- **Covariates**: `team_size`, `project_age`, `total_comment_count`.
- **Verification**: The GitHub API provides all required fields. PR events without `body` are excluded from sentiment but included in temporal metrics. No missing variables are anticipated for the open dataset.

## Statistical Methodology

### Primary Analysis (Pair-Level HLM)
1. **Unit of Analysis**: Contributor Pair (N = pairs).
2. **Metric Calculation**: Calculate `response_time_variance` and `mean_delay` for each pair. Calculate mean sentiment for each pair.
3. **Model**: Execute **Hierarchical Linear Modeling (HLM)**:
 - Level 1 (Pair): `Sentiment ~ Delay_Variance + Mean_Delay`
 - Level 2 (Project): Random intercept for `project_id` to account for clustering.
 - **Rationale**: This directly tests the hypothesis at the interaction level, avoiding ecological fallacy.

### Secondary Analysis (Project-Level Aggregation)
1. **Metric Aggregation**: Calculate `response_time_variance` and `mean_delay` for each project using the **median** of pair-level metrics (per FR-010).
2. **Correlation**: Perform **Spearman rank correlation** between project-level delay variance and cohesion score (FR-004).
3. **Regression**: Execute **Linear Regression** (OLS) with `cohesion_proxy_score` as the dependent variable and `response_time_variance`, `team_size`, `project_age`, and `total_comment_count` as independent variables (FR-005).
 - **Collinearity Check**: Compute Variance Inflation Factor (VIF). If VIF > 5 for any control, halt and warn (FR-008).
 - **Causal Framing**: Claims are strictly associational due to the observational nature of the data.

### Secondary Analysis & Corrections
- **Stratified Correlations**: Run correlations stratified by primary language (Python, JS, Go) and project size tier.
- **Multiple Comparison Correction**: Apply **Benjamini-Hochberg** procedure to control the false discovery rate (FDR) for secondary tests (FR-007).
- **Robustness Check**: Compare HLM results with project-level OLS results to ensure stability.

### Construct Validity (Validation)
- **Manual Ground Truth**: A subset of 50 comments per project will be manually coded for **'collaborative intent'** (e.g., 'I can help with that', 'Let me know if you need anything'). *Note: Criteria shifted from 'politeness' to 'substantive intent' to avoid semantic overlap with VADER.*
- **Metric**: Spearman correlation between VADER scores and manual scores. Target: ρ ≥ 0.5 (SC-005).
- **Constraint**: This step requires external human input. The pipeline will check for `data/validation/manual_ground_truth.csv`.
- **Fallback**: If manual data is missing, the pipeline generates a **synthetic** validation dataset based on the VADER distribution to test the pipeline logic, flagging results as "synthetic".

## Compute Feasibility
- **CPU-First**: All selected methods (VADER, Spearman, OLS, HLM) are computationally lightweight and will run on the GitHub Actions free-tier (limited CPU and RAM resources)..
- **Data Streaming**: For large repositories (>100k events), the ingestion script will stream data and aggregate statistics on-the-fly to avoid memory exhaustion.
- **No GPU Required**: VADER does not require a GPU. No fine-tuning of large language models is planned.

## Decision/Rationale
- **Why HLM?**: It allows modeling at the interaction level (pair) while controlling for project-level effects, resolving the ecological fallacy concern.
- **Why VADER?**: It is the standard for social media sentiment, requires no training data, and runs efficiently on CPU.
- **Why GitHub?**: It is the only open, programmatic source for large-scale software team interaction data with timestamps and text.
- **Why Median Aggregation?**: Pair-level variances can be skewed by a few extreme outliers; the median provides a more robust project-level metric (per FR-010) for the secondary analysis.
- **Why Benjamini-Hochberg?**: We are running multiple stratified tests; FDR control is more powerful than Bonferroni for this exploratory context.
- **Why 'Collaborative Intent'?**: To ensure construct validity, manual coding focuses on substantive offers of help rather than simple politeness, reducing circularity with VADER's sentiment triggers.
- **Why Synthetic Fallback?**: To ensure the pipeline is reproducible and testable on CI even when external manual data is not yet available.
