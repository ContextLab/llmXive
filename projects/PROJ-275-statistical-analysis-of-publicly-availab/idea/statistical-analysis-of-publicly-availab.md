---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

**Field**: statistics

## Research question

Is there a statistically significant correlation between aggregated movie review sentiment scores and subsequent box office revenue, after controlling for genre and production budget?

## Motivation

This study addresses the gap in understanding how consumer sentiment quantitatively predicts commercial success in the film industry. While sentiment analysis is well-studied, its specific predictive power for box office performance using public statistical profiling methods remains under-explored.

## Related work

- [Two-dimensional Sentiment Analysis of text (2014)](http://arxiv.org/abs/1406.2022v1) — Defines sentiment analysis tasks including movie ratings, providing a methodological basis for extracting opinion scores from text.
- [Statistical and Clinical Aspects of Hospital Outcomes Profiling (2007)](http://arxiv.org/abs/0710.4622v1) — Offers a framework for statistical profiling and outcome comparison, applicable to modeling industry performance metrics.

## Expected results

We expect to find a moderate positive correlation between average sentiment scores and revenue, with higher variance explained by genre-specific models. Significance will be confirmed via p-values < 0.05 in regression coefficients, requiring a sample size of N > 1000 films to achieve sufficient statistical power.

## Methodology sketch

- Download the IMDb Review Dataset from Kaggle (https://www.kaggle.com/datasets/utathya/imdb-review-dataset) using `wget`.
- Download the TMDB Movie Metadata dataset from Kaggle (https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) using `wget`.
- Merge datasets on movie title and year using `pandas` (CPU only, < 4GB RAM).
- Compute aggregate sentiment scores per film using the VADER lexicon or TextBlob (lightweight, no GPU required).
- Clean revenue and budget figures, handling missing values via listwise deletion.
- Visualize distributions of sentiment and revenue using `matplotlib` to check for outliers.
- Fit an Ordinary Least Squares (OLS) regression model predicting revenue from sentiment, budget, and genre dummies.
- Perform residual analysis to check for homoscedasticity and normality assumptions.
- Calculate Pearson correlation coefficients between sentiment and revenue within genre subsets.
- Generate summary tables and plots for final reporting within the 6-hour runtime limit.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A (no corpus provided).
- Verdict: NOT a duplicate
