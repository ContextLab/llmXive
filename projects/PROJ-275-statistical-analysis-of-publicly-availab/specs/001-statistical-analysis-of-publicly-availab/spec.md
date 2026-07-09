# Feature Specification: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

**Feature Branch**: `001-sentiment-revenue-lag-analysis`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system must successfully download, merge, and filter the TMDB 5000 Movie Dataset and IMDb Reviews datasets to create a unified, time-aligned dataset ready for analysis.

**Why this priority**: Without a clean, merged dataset containing both sentiment timestamps and revenue figures, no statistical analysis can occur. This is the foundational step for the entire project.

**Independent Test**: The pipeline can be tested by executing the data ingestion script and verifying that the output CSV contains at least 500 movies with non-null values for both `opening_weekend_revenue` and `sentiment_score` columns, along with valid `release_date` and `review_timestamp` fields.

**Acceptance Scenarios**:

1. **Given** the TMDB 5000 Movie Dataset and IMDb Reviews are available via public URLs, **When** the ingestion script runs, **Then** the merged dataset contains ≥ 500 unique movies with complete opening weekend revenue and at least 3 months of review history.
2. **Given** the merged dataset, **When** the filtering logic is applied, **Then** movies lacking revenue data or sufficient review timestamps are excluded, and the final row count is recorded.
3. **Given** the filtered dataset, **When** a sample of movies is inspected, **Then** each movie has a valid `genre` label, `opening_weekend_revenue`, and a time-series of weekly sentiment scores.

---

### User Story 2 - Temporal Lag and Correlation Analysis (Priority: P2)

The system must compute cross-correlation functions to identify the optimal time lag between sentiment and revenue for each movie, then aggregate these results by genre.

**Why this priority**: This directly addresses the core research question regarding temporal dynamics. It transforms raw time-series data into the primary statistical metric (optimal lag) required for the study.

**Independent Test**: The analysis module can be tested by running it on a synthetic dataset with known lag patterns (e.g., sentiment leads revenue by a defined temporal interval) including realistic noise structures (autocorrelation, heteroscedasticity, zero-inflation) and verifying the computed lag matches the ground truth within a tolerance of ±1 week.

**Acceptance Scenarios**:

1. **Given** a single movie with aligned sentiment and revenue time-series, **When** the cross-correlation function is computed, **Then** the lag with the maximum absolute correlation coefficient is identified and stored.
2. **Given** the full dataset of 500+ movies, **When** the lag analysis is stratified by genre using bootstrap aggregation (a sufficient number of resamples), **Then** the output includes the median lag and % confidence interval for each genre (e.g., Action, Drama).
3. **Given** the lag results, **When** a correlation plot is generated, **Then** it visually displays the relationship between sentiment and revenue at the identified optimal lag for a representative sample of movies.

---

### User Story 3 - Decay Rate Estimation and Reporting (Priority: P3)

The system must calculate the decay rate of the sentiment-revenue correlation over the theatrical run and generate summary tables and plots for the final report.

**Why this priority**: This addresses the second part of the research question (predictive power decay) and produces the final deliverables required to validate the hypothesis.

**Independent Test**: The reporting module can be tested by verifying that the generated plots correctly show a decreasing correlation trend over weeks -12 for a subset of movies defined as a synthetically generated dataset where the negative trend is mathematically guaranteed by the generation process.

**Acceptance Scenarios**:

1. **Given** the weekly sentiment-revenue correlations for weeks 1-12, **When** the decay rate is calculated, **Then** the output includes a slope coefficient representing the rate of decay for each genre.
2. **Given** the decay results, **When** a summary table is generated, **Then** it lists the mean decay rate, p-value, and sample size for each genre.
3. **Given** the full analysis results, **When** the final report is compiled, **Then** it includes the lag-decay plots and a conclusion section summarizing genre-specific lag patterns.

---

### Edge Cases

- What happens when a movie has no reviews in the 3 months prior to release? (System should exclude it entirely from the analysis pipeline, including descriptive stats requiring that window).
- How does the system handle movies with missing genre labels? (System should assign them to an "Unknown" category or exclude them from genre-stratified analysis).
- How does the system handle time-series with gaps (e.g., no reviews for a specific week)? (System should interpolate or exclude weeks with missing data from the correlation calculation).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download the TMDB 5000 Movie Dataset and IMDb Reviews datasets using `wget` and merge them on movie title and release year using `pandas` (See US-1).
- **FR-002**: The system MUST filter the merged dataset to include only movies with complete opening weekend revenue data and at least 3 months of review timestamps (See US-1).
- **FR-003**: The system MUST compute weekly sentiment scores using the VADER lexicon library without requiring GPU acceleration (See US-1, US-2).
- **FR-004**: The system MUST apply first-order differencing to both sentiment and revenue time-series to ensure stationarity, then calculate the cross-correlation function to identify the optimal lag (See US-2).
- **FR-005**: The system MUST stratify the lag analysis results by genre and compute the median lag and % confidence interval for each genre using bootstrap aggregation (sufficient resamples) (See US-2).
- **FR-006**: The system MUST apply Fisher Z-transformation to correlation coefficients before calculating the decay rate of the sentiment-revenue correlation over the -week theatrical run (See US-3).
- **FR-007**: The system MUST generate summary tables and lag-decay plots for the final report within a fixed runtime limit when processing the full filtered dataset (≥500 movies) (See US-3).

### Key Entities

- **Movie**: Represents a film with attributes including title, release year, genre, opening weekend revenue, and a time-series of weekly sentiment scores.
- **SentimentTimeSeries**: A sequence of weekly sentiment scores derived from review text, aligned with the movie's release date.
- **RevenueTimeSeries**: A sequence of weekly box office revenue figures aligned with the movie's release date.
- **LagMetric**: A statistical measure representing the optimal time delay between sentiment and revenue, identified as the lag of maximum correlation (See FR-004).
- **DecayMetric**: A statistical measure representing the rate of change in the sentiment-revenue correlation over the 12-week theatrical run, derived from Fisher Z-transformed coefficients (See FR-006).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of movies with valid lag calculations is measured against the minimum sample size requirement of N > 500 films (See FR-002, US-1).
- **SC-002**: The p-value is calculated and reported for all genres (See FR-005, US-2).
- **SC-003**: The difference in median lag between genre pairs is calculated and reported accurately (See FR-005, US-2).
- **SC-004**: The decay rate of sentiment-revenue correlation is calculated and reported for each genre (See FR-006, US-3).
- **SC-005**: The total runtime of the analysis pipeline is measured against a predefined time limit on a GitHub Actions free-tier runner (See FR-007, US-3).

## Assumptions

- **Dataset Availability**: The TMDB 5000 Movie Dataset and IMDb Reviews datasets are available via specified public URLs (e.g., Kaggle) and can be downloaded without authentication or API key restrictions.
- **Data Quality**: The merged dataset will contain at least 500 movies with complete opening weekend revenue data and sufficient review timestamps to perform the time-series analysis.
- **Methodology**: The VADER lexicon is an appropriate and validated tool for computing sentiment scores from movie review text in this context.
- **Computational Constraints**: The analysis can be completed within a reasonable runtime limit and standard RAM constraint of a GitHub Actions free-tier runner using CPU-only methods.
- **Temporal Alignment**: The release dates in the TMDB dataset and the review timestamps in the IMDb dataset can be accurately aligned to compute weekly time-series.
- **Genre Classification**: The genre labels in the TMDB dataset are sufficiently granular to support the stratified analysis (e.g., "Action", "Drama").
- **No GPU Requirement**: The VADER implementation and statistical calculations (cross-correlation, regression) do not require GPU acceleration and will run efficiently on CPU.
- **Power Limitation**: The sample size of N > 500 films is sufficient to detect the hypothesized genre-specific lag patterns with statistical significance (p < 0.05).