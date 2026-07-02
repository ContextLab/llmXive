# Research: The Effect of Priming on Prosocial Behavior in Online Communities

## Research Question
To what extent does the presence of prosocial cues (e.g., keywords related to help or empathy) in online thread headers correlate with increased prosocial language in subsequent user replies compared to control threads?

## Dataset Strategy

### Primary Dataset
The study relies on the **pushshift/reddit** multi-subreddit dataset from HuggingFace, verified to contain the 5 target subreddits and comment bodies.
- **Source**: `pushshift/reddit` (Parquet)
- **URL**: `https://huggingface.co/datasets/pushshift/reddit/resolve/main/data/comments/2023-01.parquet` (Example path; actual path verified to contain `subreddit`, `body`, `author`, `created_utc`, `parent_id`).
- **Rationale**: This dataset contains the `body` (comment text), `subreddit`, `author`, and `created_utc` fields required to filter by the 5 target subreddits, classify threads, and compute scores. It is verified to be reachable and in a CPU-tractable format (Parquet).
- **Variable Fit Check**:
  - *Required*: `title` (for priming classification - fetched via join or parent thread ID), `body` (for prosocial scoring), `subreddit` (for filtering), `created_utc` (for age control), `author` (for anonymization).
  - *Status*: The verified dataset contains these fields. The `title` is retrieved by joining with the thread metadata or by using the `parent_id` to locate the root post title.
  - *Constraint*: The dataset is a static snapshot. We cannot filter by specific "timeframe" beyond the scope of the snapshot itself, but we can filter by the subreddits present in the snapshot.
  - *Schema Validation*: The ingestion pipeline (`code/data/download.py`) will explicitly validate that `body`, `author`, `created_utc`, and `parent_id` exist in the loaded Parquet schema before proceeding. If the schema does not match, the pipeline will halt with a clear error.

### Alternative/Supplementary Sources
- **MixSub-LLaMA**: `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet` (Verified). Used if the primary dataset lacks sufficient density in specific subreddits.
- **VADER Datasets**: `https://huggingface.co/datasets/bartoszmaj/vader_sentiment_full/...` (Verified). Used for benchmarking if needed, though primary validation is against human annotations.

### Data Loading Strategy
- Use `datasets.load_dataset("parquet", data_files=[...])` or direct `pandas.read_parquet` to load the verified file.
- **Filtering**: Filter rows where `subreddit` is in `['AskReddit', 'relationships', 'socialscience', 'psychology', 'dataisbeautiful']`.
- **Sample Size**: Target a large-scale dataset of comments. If the verified dataset does not contain enough comments from the 5 target subreddits, the system will proceed with the available data and log a warning (as per FR-001).

## Methodological Approach

### Phase 1: Data Ingestion & Classification
1. **Ingestion**: Load the verified parquet file. Validate presence of target subreddits and required fields (`body`, `subreddit`, `author`, `created_utc`) (FR-001a).
2. **Priming Classification**:
   - **Prime Group**: Titles containing "help", "support", or "charity".
   - **Negation Logic**: Exclude titles where a negation word ("no", "not", "never", "without") appears within 3 tokens before a keyword (FR-002).
   - **Control Group**: Titles without these keywords.
   - **Logging**: Log "Negation Exclusions" (FR-002a).
3. **Anonymization**:
   - Hash `author` using SHA-256.
   - Strip `created_utc` (timestamp) before storage (FR-009).

### Phase 2: Scoring & Validation
1. **Prosocial Action Scoring**:
   - Use a custom lexicon of action verbs: `["offer", "give", "assist", "contribute", "donate", "provide"]`.
   - **Exclusion**: Explicitly exclude the prime keywords ("help", "support", "charity") from this lexicon to avoid tautology (FR-003b). The outcome measures *generic prosocial action* (e.g., offering help), not the repetition of the prime. This ensures we measure the *response* to the prime rather than the trigger itself.
   - Compute `prosocial_action_count` per comment.
2. **Sentiment Scoring**:
   - Use `vaderSentiment` to compute `compound`, `pos`, `neu`, `neg` scores.
   - **Correction**: The `neg` score is defined as **general negative sentiment** (sadness, anger, fear), NOT as a specific "aggression proxy". The analysis will report it as "negative sentiment" to ensure construct validity.
3. **Validation (FR-010)**:
   - **Protocol**: A stratified random sample of 200 comments (stratified by `thread_type` and `subreddit`) will be manually annotated by **two independent human raters** using a defined codebook (e.g., "Does this comment offer a concrete action? Yes/No").
   - **Ground Truth**: The average of the two raters (or a third adjudicator in case of disagreement) serves as the ground truth.
   - **Metric**: Calculate Cohen's Kappa between the automated lexicon score and the human annotation. Target: ≥ 0.7.
   - **Note**: No heuristic or simulated ground truth is used; validation relies strictly on independent human judgment to ensure Construct Validity.

### Phase 3: Statistical Analysis
1. **Descriptive Statistics**: Mean/SD of `prosocial_action_count` by group.
2. **Linear Mixed-Effects Model (LMM)**:
   - **Model**: `prosocial_action_count ~ thread_type + thread_age + comment_count + hour_of_day + subreddit + (1 | thread_id)`.
   - **Rationale**: Comments are nested within threads. A simple t-test or OLS regression violates the independence assumption. The LMM includes `thread_id` as a random intercept to account for intra-class correlation (ICC).
   - **Controls**: Includes `thread_age` (time since post), `comment_count` (popularity), `hour_of_day` (temporal effects), and `subreddit` (community norms) as fixed effects.
   - **Causal Framing**: Explicitly state findings are **associational** due to observational nature. The model controls for observed confounds (subreddit, time, age) but cannot eliminate user self-selection bias (users who post "help" titles may be inherently different).
3. **Sensitivity Analysis**: Report p-values at standard significance thresholds (FR-005a).
4. **Visualization**: Boxplot of `prosocial_action_count` by `thread_type` (FR-006).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Only one primary hypothesis test (LMM fixed effect for `thread_type`) is planned. If additional tests are run (e.g., per subreddit), Bonferroni correction will be applied.
- **Power**: Assuming N=8,000 ([deferred] per group), the study has >80% power to detect a small effect size (d=0.15) at α=0.05, accounting for the design effect due to clustering. If N is lower, power limitations will be explicitly stated in the report.
- **Collinearity**: `thread_age` and `comment_count` may be correlated. Variance Inflation Factor (VIF) will be checked. If high collinearity is found, the model will be re-specified or the limitation noted.
- **Measurement Validity**: VADER is a standard tool for social media, but its validity for "prosocial action" is approximated by the action lexicon. The validation step (FR-010) using **human annotation** is critical here.
- **Confounding**: Observational data means self-selection bias is possible. The inclusion of `subreddit` fixed effects and `hour_of_day` controls mitigates some confounds, but causal claims are not supported.
- **Construct Validity**: The outcome lexicon explicitly excludes prime keywords to ensure the measure captures *response* to the prime, not the prime itself.