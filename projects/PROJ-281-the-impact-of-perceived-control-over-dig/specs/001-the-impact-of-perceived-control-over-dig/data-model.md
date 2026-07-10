# Data Model: 001-perceived-control-anxiety

## Overview

This document defines the data structures used throughout the pipeline, ensuring strict separation between text-derived features (anxiety) and metadata-derived features (control).

## Entity Definitions

### 1. SocialPost (Raw)
The raw record ingested from the dataset.
- `post_id` (string): Unique identifier for the post.
- `text` (string): The content of the post.
- `timestamp` (datetime): Time of posting.
- `user_id` (string): Unique identifier for the user.
- `metadata` (dict): Additional fields (e.g., `filter_applied`, `likes`, `retweets`). Note: `filter_applied` is a raw field if available.

### 2. AnxietyScoreRecord
Output of the NLP inference step.
- `post_id` (string): Foreign key to `SocialPost`.
- `anxiety_score` (float): Continuous score [0.0, 1.0].
- `confidence_score` (float): Maximum probability of the predicted class [0.0, 1.0].
- `predicted_class` (string): The emotion class predicted by the model.
- `excluded` (boolean): True if `confidence_score` < 0.6.
- **File Mapping**: Saved to `data/processed/scoring_results.csv`.

### 3. ControlProxyRecord
Output of the metadata extraction step.
- `post_id` (string): Foreign key to `SocialPost`.
- `control_proxy` (float): Calculated score based on metadata.
- `filter_flag` (boolean): Derived from raw `filter_applied` metadata (True if present).
- `timestamp_regularity` (float): Metric of posting consistency (0.0 to 1.0).
- **File Mapping**: Saved to `data/processed/proxy_results.csv`.

### 4. AnalysisResult
Final merged record for statistical testing.
- `post_id` (string)
- `anxiety_score` (float)
- `control_proxy` (float)
- `valid` (boolean): True if `anxiety_score` is valid and confidence >= 0.6.
- **File Mapping**: Saved to `data/processed/final_analysis.csv`.

## Processing Pipeline Flow

1. **Ingest**: `SocialPost` (Raw) -> `data/raw/ingested.csv`
2. **Score**: `SocialPost` -> `anxiety_scoring.py` -> `AnxietyScoreRecord` -> `data/processed/scoring_results.csv`
3. **Proxy**: `SocialPost` -> `proxy_extractor.py` -> `ControlProxyRecord` -> `data/processed/proxy_results.csv`
4. **Merge**: Join `AnxietyScoreRecord` and `ControlProxyRecord` on `post_id`.
5. **Filter**: Remove rows where `confidence_score` < 0.6.
6. **Analyze**: `AnalysisResult` -> `statistical_test.py` -> `AnalysisResult` (final) -> `data/processed/final_analysis.csv`.

## Data Hygiene Rules

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: Every file in `data/` is checksummed (SHA-256).
- **PII**: `user_id` is hashed or anonymized before any analysis if it contains PII.
