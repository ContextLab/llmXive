# Data Model: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is stored in memory as Pandas DataFrames or NumPy arrays, and persisted as Parquet, CSV, or NumPy binary files.

## 2. Core Entities

### 2.1 Raw Track Metadata
Derived from the join of MPD and MusicBrainz.

| Column | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `track_id` | `str` | Unique identifier for the track. | MPD / MusicBrainz |
| `artist_name` | `str` | Name of the artist. | MusicBrainz |
| `album_name` | `str` | Name of the album. | MusicBrainz |
| `title` | `str` | Track title. | MusicBrainz |
| `release_year` | `int` | Year of release. | MusicBrainz |
| `genres` | `list[str]` | List of genre tags (multi-label). | MusicBrainz |
| `play_count` | `int` | Number of times played (if available in MPD). | MPD |

### 2.2 Yearly Genre Embeddings
Output of the Word2Vec training step (derived from Global Model).

| Column | Type | Description |
| :--- | :--- | :--- |
| `year` | `int` | Calendar year. |
| `genre` | `str` | Canonical genre name. |
| `embedding` | `ndarray` | 100-dimensional vector (stored as list of floats in CSV/Parquet, or binary in .npy). |

### 2.3 Similarity Metrics
Output of the similarity calculation step.

| Column | Type | Description |
| :--- | :--- | :--- |
| `year` | `int` | Calendar year. |
| `mean_off_diagonal_similarity` | `float` | Average cosine similarity between distinct genre vectors. |
| `intra_genre_variance` | `float` | Variance of similarity scores within the same genre (optional). |
| `n_genres` | `int` | Number of genres represented in that year. |

### 2.4 Regression Results
Output of the statistical testing step (Updated for Cook's Distance).

| Column | Type | Description |
| :--- | :--- | :--- |
| `model_type` | `str` | "Full", "Outlier_Removed", "Shuffled_Order". |
| `slope` | `float` | Estimated coefficient for `year`. |
| `std_err` | `float` | Newey-West HAC standard error. |
| `p_value` | `float` | Uncorrected p-value. |
| `ci_lower` | `float` | Lower bound of 95% CI. |
| `ci_upper` | `float` | Upper bound of 95% CI. |
| `n_samples` | `int` | Number of years used in the regression. |
| `outlier_indices` | `str` | JSON string of outlier indices (if applicable). |

## 3. File Formats

| File | Format | Description |
| :--- | :--- | :--- |
| `data/raw/mpd.parquet` | Parquet | Raw MPD data. |
| `data/raw/musicbrainz.parquet` | Parquet | Raw MusicBrainz data. |
| `data/derived/metadata.csv` | CSV | Cleaned track metadata (year, genre, track_id). |
| `data/derived/global_model.w2v` | Gensim | Global Word2Vec model. |
| `data/derived/embeddings/{year}.npy` | NumPy | Genre embedding matrix for a specific year. |
| `data/derived/yearly_similarity.csv` | CSV | Aggregated similarity metrics. |
| `data/derived/sensitivity_report.csv` | CSV | Regression results for robustness checks. |
| `data/derived/pipeline_log.txt` | Text | Execution log. |

## 4. Data Flow

1.  **Ingest**: Raw Parquet -> `metadata.csv` (filtered, joined).
2.  **Embed**: `metadata.csv` (all years) -> `global_model.w2v` -> `embeddings/{year}.npy`.
3.  **Similarity**: `embeddings/{year}.npy` -> `yearly_similarity.csv`.
4.  **Regression**: `yearly_similarity.csv` -> `sensitivity_report.csv` (Full, Outlier, Shuffled).
5.  **Viz**: `yearly_similarity.csv` -> `similarity_trend.png`, `genre_similarity_heatmap.html`.