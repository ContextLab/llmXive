# Data Model

## Entities

### Comment
- `comment_id`: Unique identifier (string).
- `thread_id`: Identifier for the parent thread (string).
- `user_id`: SHA-256 hash of the username (string).
- `body`: Text content of the comment (string).
- `thread_type`: Classification ("Prime" or "Control") (string).
- `subreddit`: Source subreddit (string).
- `created_utc`: Original timestamp (int, removed in final output).
- `thread_age`: Age of thread in seconds (int).
- `comment_count`: Number of comments in thread (int).
- `prosocial_action_count`: Count of prosocial actions (int).
- `neg_score`: Negative sentiment score (float).

## Schemas
- `dataset.schema.yaml`: Raw/processed dataset schema.
- `scored.schema.yaml`: Scored dataset schema.
- `output.schema.yaml`: Final report schema.
