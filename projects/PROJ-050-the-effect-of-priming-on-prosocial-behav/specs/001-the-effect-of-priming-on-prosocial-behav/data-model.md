# Data Model: The Effect of Priming on Prosocial Behavior

## Core Entities

### Thread (Parent)
| Field | Type | Description |
|-------|------|-------------|
| `thread_id` | string | Unique identifier (`link_id` from comment). |
| `subreddit` | string | Subreddit name (`AskReddit`, `science`, `relationships`). |
| `thread_type` | string (enum) | **Prime** / **Control** – *only defined if a title field is available*. Currently `null` pending dataset revision. |
| `title` | string | **Required for priming** – **absent** in the verified dataset. |

### Comment (Child)
| Field | Type | Description |
|-------|------|-------------|
| `comment_id` | string | Comment identifier (`id`). |
| `user_id` | string | SHA‑256 hash of original `author`. |
| `thread_id` | string | Foreign key to `Thread.thread_id`. |
| `body` | string | Comment text (`body`). |
| `vader_compound` | number (‑1 → 1) | VADER compound sentiment score. |
| `prosocial_intent_score` | integer ≥ 0 | Count of distinct prosocial lexicon matches (excluding prime words). |
| `thread_length` | integer ≥ 0 | Character count of `body`. |
| `user_tenure` | integer ≥ 0 | Days since account creation, derived from `created_utc` before timestamp removal. |
| `created_utc` | *removed* | Stripped for privacy; used only to compute `user_tenure`. |
| `subreddit` | string | Redundant copy for convenience (random effect). |

## Data Flow
1. **Raw Streaming** → `data/raw/streamed_records.jsonl` (not persisted, streamed).  
2. **Ingestion & Anonymization** → `data/processed/anonymized.csv` (fields: `comment_id`, `user_id`, `thread_id`, `body`, `subreddit`, `thread_type` (nullable), `user_tenure`).  
3. **Scoring** → `data/processed/scored.csv` (adds VADER & prosocial counts).  
4. **Human Annotation** → `data/processed/annotations.csv` (gold‑standard labels).  
5. **Analysis** → `data/processed/model_results.json` (LMM coefficients, p‑values, convergence).  

## Constraints & Invariants
- `comment_id` unique.  
- `user_id` matches SHA‑256 pattern `^[a-f0-9]{64}$`.  
- No plaintext usernames or timestamps in any processed file.  
- `prosocial_intent_score` ≥ 0.  
- `vader_compound` in `[-1, 1]`.  
- `user_tenure` ≥ 0 (derived).  
- **Lexicon Independence**: Prosocial lexicon excludes prime words (`thank`, `help`, `support`, `care`).  

---

