# Data Model: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final statistical reporting. All data is processed in memory using `pandas` DataFrames and serialized to Parquet/CSV for intermediate storage. The model has been revised to reflect that revenue is a static scalar per movie, not a time-series.

## Entity Definitions

### 1. Movie (Core Entity)
Represents a single film in the dataset.
- **Attributes**:
  - `movie_id`: Unique identifier (derived or from source).
  - `title`: String (normalized).
  - `release_date`: Date (YYYY-MM-DD).
  - `opening_weekend_revenue`: Float (USD). **Static scalar**.
  - `genres`: List of strings (e.g., `["Action", "Sci-Fi"]`). **Note**: Missing genres are assigned "Unknown".
  - `runtime_minutes`: Integer.
  - `budget`: Float (optional, for descriptive stats).

### 2. Review
Represents a single user review.
- **Attributes**:
  - `review_id`: Unique identifier.
  - `movie_title`: String (join key, normalized).
  - `review_date`: Date (YYYY-MM-DD).
  - `text`: String (raw review text).
  - `sentiment_compound`: Float (-1.0 to 1.0).
  - `sentiment_pos`: Float.
  - `sentiment_neg`: Float.
  - `sentiment_neu`: Float.

### 3. WeeklyTimeSeries
Aggregated view of sentiment per week relative to release. **Revenue is not included here as a time-series; it is a static reference in the Movie entity.**
- **Attributes**:
  - `movie_id`: Foreign key.
  - `week_offset`: Integer (-4 to +12). -4 = 4 weeks before release.
  - `avg_sentiment`: Float.
  - `review_count`: Integer.
  - **Note**: No `revenue` field. Revenue is accessed via `movie_id` from the Movie entity.

### 4. AnalysisResult
Output of the statistical tests.
- **Attributes**:
  - `genre`: String.
  - `optimal_lag_weeks`: Integer.
  - `max_correlation`: Float (Population-level correlation at optimal lag).
  - `lag_ci_lower`: Float.
  - `lag_ci_upper`: Float.
  - `decay_slope`: Float (Fisher Z slope of aggregate correlations).
  - `decay_p_value`: Float.
  - `sample_size`: Integer.

## Data Flow

1. **Raw Ingestion**: `movies_2025_filtered.tsv` + `imdb_reviews.parquet` -> `raw_merged.parquet`.
2. **Cleaning**: Filter nulls, align dates (fuzzy title match), assign "Unknown" genre -> `cleaned_movies.parquet`.
3. **Feature Engineering**: Weekly aggregation of sentiment -> `weekly_timeseries.parquet`.
4. **Analysis**: Lagged Correlation Profile and Aggregate Decay Trend -> `analysis_results.csv`.
5. **Reporting**: `final_report.json` (for plots).

## Constraints & Validation

- **Date Alignment**: All dates must be valid ISO 8601.
- **Revenue**: Must be > 0 for inclusion in analysis.
- **Sentiment**: Must be in range [-1, 1].
- **Genre**: Must be non-empty; "Unknown" if missing.
- **Schema Validation**: All intermediate and final outputs must pass validation against `contracts/dataset.schema.yaml` and `contracts/analysis_results.schema.yaml`.