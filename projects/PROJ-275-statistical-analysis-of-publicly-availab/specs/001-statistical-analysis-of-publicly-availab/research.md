# Research: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

## Problem Statement

The study investigates the temporal dynamics between consumer sentiment (derived from review text) and box office revenue. Specifically, it seeks to determine:
1. The optimal time lag (in weeks) where sentiment most strongly predicts opening weekend revenue.
2. The rate at which this predictive correlation decays over the theatrical run (weeks 1-12).
3. How these dynamics vary by movie genre.

**Critical Data Constraint**: The available datasets (TMDB 5000, StanfordNLP IMDb) provide **static** opening weekend revenue per movie, but **time-varying** review sentiment. Therefore, standard Cross-Correlation Functions (CCF) on per-movie series are mathematically invalid (cannot compute CCF on a scalar). The methodology has been revised to a **Lagged Correlation Profile** approach: calculating the correlation between the *static* revenue vector of the population and the *weekly* sentiment vector of the population for each time offset.

## Dataset Strategy

The analysis relies on two primary data sources. The plan strictly adheres to the "Verified datasets" block to ensure reproducibility and avoid fabricated sources.

| Dataset Role | Source Name | Verified URL | Usage Strategy |
|--------------|-------------|--------------|----------------|
| **Movie Metadata & Revenue** | TMDB 5000 (Filtered) | ` | Provides `title`, `release_date`, `opening_weekend_revenue`, and `genres`. |
| **Review Text** | IMDb Reviews | ` | Provides `review_text` and `review_date` (or timestamp). **Note**: Requires fuzzy title matching to join with TMDB. |
| **Fallback** | None | N/A | If the primary English dataset lacks `movie_title` or `release_date` fields, the analysis halts. No non-English fallbacks are used as VADER is English-specific. |

**Critical Data Fit Assessment**:
- **TMDB Source**: Contains revenue and release dates.
- **IMDb Source**: The StanfordNLP dataset is a standard sentiment benchmark. **Risk**: It lacks explicit `movie_title` or `release_date` fields required for precise temporal alignment.
- **Gap Handling**: The implementation will perform a **Fuzzy Title Alignment** (Levenshtein distance) between IMDb review text metadata (if available) or inferred titles and TMDB titles. If a movie cannot be aligned with high confidence, it is excluded. If the dataset completely lacks linking keys, the analysis halts with a "Data Gap" error.

*Decision*: The implementation will first validate the schema of the verified datasets. If the IMDb dataset lacks the necessary linking keys (title/year) to join with TMDB, the plan will flag this as a **blocking data gap** and halt execution.

## Methodological Approach

### 1. Data Preprocessing (FR-001, FR-002)
- **Ingestion**: Use `pandas` to load TSV and Parquet files.
- **Alignment**: Join on `title` using fuzzy matching (threshold > 0.85) and `release_year`.
- **Filtering**: Retain only movies with `opening_weekend_revenue` > 0 and at least 3 months of review history.
- **Genre Handling**: Movies with missing genre labels are assigned "Unknown" to ensure no data loss in stratified analysis.
- **Time-Series Construction**: Bin reviews into weekly buckets relative to `release_date` (weeks -4 to +12).

### 2. Sentiment Scoring (FR-003)
- **Tool**: `nltk.sentiment.vader.VaderSentiment`.
- **Rationale**: CPU-tractable, no GPU required, validated for short text (reviews).
- **Output**: Weekly `sentiment_score` (compound score) per movie.

### 3. Temporal Lag Analysis (FR-004, FR-005) - Revised
- **Method**: **Lagged Correlation Profile**.
 - For each movie, we have a static revenue value $R$ and a time-series of sentiment $S_t$.
 - We cannot compute CCF on $R$ (scalar) and $S_t$ (vector).
 - Instead, we compute the correlation $r_t$ between the **population vector of revenues** and the **population vector of sentiments at week t**.
 - We repeat this for each week $t$ (lag) in the window (-4 to +4).
 - The "Optimal Lag" for a genre is the lag $t$ where the median $r_t$ (across movies in that genre) is maximized.
- **Stratification**: Aggregate results by `genre`.
- **Confidence**: Use bootstrap aggregation (e.g., 1000 resamples) to compute 95% confidence intervals for the optimal lag per genre.

### 4. Decay Rate Estimation (FR-006) - Revised
- **Method**: **Aggregate Correlation Trend**.
 - For each week $t$ in the theatrical run (weeks 1-12), calculate the aggregate correlation coefficient $r_t$ between the vector of all movies' revenues and the vector of all movies' sentiments at week $t$.
 - Apply Fisher Z-transformation to these aggregate $r_t$ values.
 - Fit a linear model: $Z(r_t) \sim t$.
 - **Metric**: The slope coefficient represents the decay rate of the predictive power over time.
 - **Significance**: Report p-value for the slope.
- **Rationale**: This avoids the invalid per-movie regression (N=1) and correctly models the decay of the *population-level* relationship.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: When testing lag differences across multiple genres, a Bonferroni or False Discovery Rate (FDR) correction will be applied to the p-values to control family-wise error rate.
- **Power Limitation**: The sample size (N > 500) is assumed sufficient for genre-stratified analysis, but power will be explicitly calculated for smaller genres (e.g., "Animation" vs. "Action"). If a genre has < 30 movies, the result will be flagged as underpowered.
- **Causal Inference**: The study is observational. Claims will be framed as "associational" or "predictive," not causal. No randomization strategy exists; identification relies on temporal precedence (sentiment precedes revenue).
- **Collinearity**: If a genre is defined by a variable that is also a predictor (e.g., "Horror" is both a genre and a sentiment driver), collinearity will be acknowledged, and independent effects will not be claimed.
- **Measurement Validity**: VADER is cited as the standard for social media/review sentiment, though its validity for movie-specific sarcasm is a known limitation.
- **Spec-Data Mismatch Note**: The original spec (FR-004) requested CCF on time-series. This is impossible with static revenue. The revised "Lagged Correlation Profile" is the only valid statistical approximation for this data structure. This is a necessary adaptation, not an invention of new requirements.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **CPU-only execution** | GitHub Actions free tier has no GPU. VADER and statistical tests are CPU-efficient. |
| **Bootstrap for CI** | Parametric assumptions for lag distributions are unknown; non-parametric bootstrap is robust. |
| **Fisher Z-transformation** | Correlation coefficients are not normally distributed; Z-transformation is required for valid regression on decay rates. |
| **Lagged Correlation Profile** | Required because revenue is static. CCF on scalar is invalid. This method computes population-level correlation per lag. |
| **Aggregate Decay Trend** | Required because per-movie regression on static revenue is invalid (N=1). This method computes decay of population correlation. |
| **Fuzzy Title Alignment** | Required because the verified IMDb dataset lacks explicit movie titles/dates for direct joining. |
| **"Unknown" Genre Handling** | Required to prevent data loss and satisfy the "Genre-Stratified" analysis requirement for all movies. |