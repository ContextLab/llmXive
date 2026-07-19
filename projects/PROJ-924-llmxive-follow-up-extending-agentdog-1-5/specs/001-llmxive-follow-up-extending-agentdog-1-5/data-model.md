# Data Model

## Taxonomy
- `id`: string
- `category`: string
- `examples`: list of strings
- `centroid_embedding`: list of floats (384 dim)

## Log Entry
- `log_id`: string (UUID)
- `text`: string
- `timestamp`: datetime
- `source`: string

## Drift Result
- `log_id`: string
- `drift_score`: float (0.0 to 2.0)
- `review_flag`: boolean
