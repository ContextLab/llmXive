# Data Model: The Effect of Priming on Prosocial Behavior in Online Communities

## Overview
This document defines the schema for data artifacts used in the pipeline. All data is stored in CSV or Parquet format.

## Entity Definitions

### 1. Raw Comment (Input)
Derived from the verified HuggingFace dataset.
- `link_id`: Unique thread identifier (string).
- `parent_id`: ID of the parent comment/thread (string).
- `author`: Username (string, to be hashed).
- `created_utc`: Unix timestamp (integer).
- `subreddit`: Subreddit name (string).
- `title`: Thread title (string, only for root comments).
- `body`: Comment text (string).

### 2. Anonymized Comment (Intermediate)
After ingestion and anonymization.
- `comment_id`: Unique identifier (SHA-256 hash of `link_id` + `parent_id` + `created_utc`).
- `thread_id`: Hash of `link_id` (string).
- `user_id`: SHA-256 hash of `author` (string).
- `thread_age`: Days since `created_utc` (float).
- `subreddit`: Subreddit name (string).
- `body`: Comment text (string).
- `thread_type`: "Prime" or "Control" (string).
- `negation_excluded`: Boolean (True if title had keyword but failed negation rule).
- `comment_count`: Number of comments in the thread (integer).

### 3. Scored Comment (Final Analysis Data)
After scoring.
- `comment_id`: (string).
- `thread_id`: (string).
- `user_id`: (string).
- `thread_age`: (float).
- `subreddit`: (string).
- `thread_type`: (string).
- `neg_score`: VADER `neg` component (float, 0-1).
- `prosocial_action_count`: Integer count of action verbs (int).
- `compound`: VADER compound score (float).
- `comment_count`: (integer).

## Relationships
- **Thread**: A `thread_id` groups multiple `Comment` rows.
- **User**: A `user_id` groups multiple `Comment` rows (potentially across threads).
- **Subreddit**: A categorical grouping variable.

## Constraints
- **PII**: No plaintext `author` or raw `created_utc` in `data/processed/`.
- **Integrity**: `thread_age` must be non-negative. `neg_score` must be in [0, 1]. `comment_count` must be positive.
- **Completeness**: `thread_type` must be "Prime" or "Control".

