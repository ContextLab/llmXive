# Data Model: The Effect of Priming on Prosocial Behavior

## Entities & Relationships

### Thread (Parent)
Represents the Reddit post that provides the "Prime" or "Control" condition.
*   `thread_id` (string): Unique identifier (e.g., `t3_abc123`).
*   `title` (string): The title of the post (used for regex classification).
*   `subreddit` (string): The subreddit name (e.g., "AskReddit").
*   `thread_type` (string): Enum: `['Prime', 'Control']`. Derived from title regex.

### Comment (Child)
Represents the user reply, the unit of analysis.
*   `comment_id` (string): Unique identifier (e.g., `t1_xyz789`).
*   `user_id` (string): SHA-256 hash of the original username.
*   `thread_id` (string): Foreign key to `Thread`.
*   `text` (string): The comment body (truncated or cleaned if necessary).
*   `vader_compound` (float): VADER sentiment score.
*   `prosocial_intent_score` (float): Count of prosocial words from a **distinct** lexicon (excluding prime words).
*   `thread_length` (integer): Character or word count of the comment.
*   **Note**: `user_tenure` is **removed** from the dataset and model due to data infeasibility.

## Data Flow

1.  **Raw Ingestion**: `data/raw/hf_dump.jsonl` (Original Hugging Face data).
2.  **Anonymization**: `data/processed/anonymized.csv` (SHA-256 hashed, timestamps removed).
3.  **Scoring**: `data/processed/scored.csv` (Added VADER and distinct prosocial counts).
4.  **Validation**: `data/processed/annotations.csv` (Human labels).
5.  **Analysis**: `data/processed/model_results.json` (LMM coefficients, p-values).

## Constraints & Invariants

*   **Uniqueness**: `comment_id` is unique.
*   **Referential Integrity**: Every `comment.thread_id` must exist in `Thread`.
*   **Privacy**: No raw usernames or exact timestamps in `data/processed`.
*   **Completeness**: `prosocial_intent_score` >= 0.
*   **Range**: `vader_compound` in [-1, 1].
*   **Lexicon Independence**: The prosocial lexicon **must not** contain the prime words ('thank', 'help', 'support', 'care').

## Derived Fields

*   `thread_type`: `1` if `re.search(r'(thank|help|support|care)', title, re.I)` else `0`.
*   `prosocial_intent_score`: `sum(1 for word in text.split() if word.lower() in DISTINCT_LEXICON)`.
*   `thread_length`: `len(text)`.
