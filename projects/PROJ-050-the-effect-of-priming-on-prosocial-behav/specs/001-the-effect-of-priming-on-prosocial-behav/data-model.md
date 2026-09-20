# Data Model: The Effect of Priming on Prosocial Behavior (Association Study)

## Entity Definitions

### 1. Thread
Represents the parent post that may contain the "prime".
- **Attributes**:
  - `thread_id` (str): Unique identifier (e.g., `t3_xxxxx`).
  - `title` (str): The text of the post.
  - `subreddit` (str): Subreddit name (e.g., `AskReddit`).
  - `thread_type` (str): Classification result (`'Prime'` or `'Control'`).
    - *Logic*: `Prime` if `title` matches regex `/(thank|help|support|care)/i`.
  - `created_utc` (float): Unix timestamp of creation (used for tenure calculation, **then discarded**).

### 2. Comment
Represents the user response being analyzed.
- **Attributes**:
  - `comment_id` (str): Unique identifier (e.g., `t1_xxxxx`).
  - `user_id` (str): SHA-256 hash of the original username (anonymized).
  - `thread_id` (str): Foreign key to `Thread`.
  - `body` (str): The text of the comment.
  - `vader_score` (float): Compound sentiment score from VADER (-1 to 1).
  - `prosocial_keyword_count` (int): Count of prosocial keywords in `body`.
  - `user_tenure` (float): Days between user creation (or first comment) and comment creation. **This is a derived relative metric; raw timestamps are not stored.**
  - `subreddit` (str): Subreddit name (denormalized for the model).

## Data Flow

1.  **Raw Ingestion**: `data/raw/pushshift_raw.jsonl` (or similar).
2.  **Anonymization & Filtering**:
    - Filter by subreddit and date.
    - Hash `user_id`.
    - Calculate `user_tenure` using `created_utc` and `author_created_utc` (or proxy).
    - **Discard** `created_utc` and `author_created_utc` from the output.
    - Output: `data/processed/anonymized.csv`.
3.  **Scoring**:
    - Apply VADER and Keyword Count.
    - Output: `data/processed/scored.csv`.
4.  **Annotation Sample**:
    - Randomly select a subset of rows.
    - Output: `data/annotations/sample_200.csv` (for manual review) and `data/annotations/labels.json` (simulated or loaded).
5.  **Analysis**:
    - Load `scored.csv`.
    - Fit GLMM.
    - Output: `artifacts/results.json`.

## Data Constraints

- **Anonymity**: `user_id` must never appear in plaintext.
- **Missing Data**: If `user_tenure` cannot be calculated (missing creation date), the value will be set to `NaN` and the model will handle missingness (e.g., imputation with mean or exclusion, documented in code).
- **N Limits**: If `Prime` or `Control` groups have < 100 samples, the model will fail to converge. The pipeline will report this as a "Data Insufficiency" error.

## Schema Validation

The `data/processed/scored.csv` must conform to `contracts/scored_data.schema.yaml`.
The `artifacts/results.json` must conform to `contracts/model_results.schema.yaml`.