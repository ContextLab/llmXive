# Data Model: The Effect of Priming on Prosocial Behavior in Online Communities

## 1. Entities & Relationships

### Thread
A conversation unit identified by a unique `thread_id`.  
* **Attributes**: `thread_id` (str), `subreddit` (str), `title` (str), `created_utc` (str, **used only for computing `thread_age`**, then removed), `comment_count` (int).  
* **Derived**: `thread_type` (str: “Prime” | “Control”).

### Comment
A response within a thread.  
* **Attributes**: `comment_id` (str), `thread_id` (str, FK), `user_id` (str, hashed), `body` (str), `created_utc` (str, stripped after `thread_age` calculation).  
* **Derived**: `prosocial_action_count` (int), `compound` (float), `pos` (float), `neu` (float), `neg` (float), `neg_score` (float = `neg` component).

### SentimentScore
A derived record for analysis.  
* **Attributes**: `comment_id`, `thread_id`, `neg_score` (float), `prosocial_action_count` (int).

## 2. Data Flow

1. **Raw Input**: Parquet file from HuggingFace.  
2. **Anonymized**: `user_id` = SHA‑256(author), timestamps stripped **after** `thread_age` is computed.  
3. **Classified**: `thread_type` added based on title keywords.  
4. **Scored**: `prosocial_action_count` and VADER scores added.  
5. **Analysis**: Aggregated by `thread_type` for LMM.

## 3. Schema Definitions

### Input Schema (Raw Reddit)

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique identifier for the Reddit post/comment. |
| `title` | string | Thread title (used for priming classification). |
| `body` | string | Comment text. |
| `author` | string | Original username (hashed later). |
| `created_utc` | integer | Unix timestamp (used to compute `thread_age`). |
| `subreddit` | string | Subreddit name. |
| `parent_id` | string | Optional parent identifier for threading. |

### Processed Schema (Final Analysis Table)

| Column | Type | Description |
| :--- | :--- | :--- |
| `comment_id` | string | Unique ID for the comment. |
| `thread_id` | string | Unique ID for the parent thread. |
| `user_id` | string | SHA‑256 hash of original author. |
| `subreddit` | string | Name of the subreddit (e.g., 'AskReddit'). |
| `thread_type` | string | “Prime” or “Control”. |
| `body` | string | The text content of the comment. |
| `prosocial_action_count` | integer | Count of prosocial action verbs in the comment. |
| `neg_score` | number | VADER negative sentiment component (0‑1). |
| `compound` | number | VADER compound sentiment score. |
| `thread_age` | number | Age of the thread in hours (computed **before** timestamp removal). |
| `comment_count` | integer | Total number of comments in the thread. |

## 4. Anonymization Protocol

* **Usernames**: Replaced with `SHA256(author)[:16]`.  
* **Timestamps**: Used only to compute `thread_age`; the original `created_utc` column is then removed from stored files.  
* **PII Scan**: Final output must pass a regex scan for common email/username patterns to ensure zero plaintext PII.  

## 5. Modeling Considerations

* The primary Linear Mixed‑Effects Model includes a random intercept for `thread_id`.  
* Inclusion of a `user_id` random intercept is **conditional**: after fitting the base model, the variance component for `user_id` is inspected. If it is positive, `user_id` appears in both Prime and Control groups, and the model converges, a second model with `(1|user_id)` is fit. Otherwise, the `user_id` term is omitted and a warning is logged. This safeguards against singular fits and respects the observational design constraints.  
