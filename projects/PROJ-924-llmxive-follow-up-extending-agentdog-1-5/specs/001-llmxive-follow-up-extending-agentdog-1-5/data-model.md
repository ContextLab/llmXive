# Data Model: Zero-Shot Drift Detection for AgentDoG 1.5

## 1. Entities

### Log
Represents a single log entry from the input dataset.
-   `log_id`: UUID (generated from dataset `id` or hash)
-   `text`: String (raw log content, e.g., `contents` from ATBench)
-   `timestamp`: Datetime (if available in source; otherwise, derived deterministically from `log_id` hash using SHA256 to ensure reproducibility without synthetic randomness).
-   `source_category`: String (e.g., `risk_source` from ATBench, used for ground truth "Known" vs "Novel" classification)

### Taxonomy
Represents the safety categories and their centroids.
-   `category`: String (unique label, e.g., "Prompt Injection", "Data Exfiltration")
-   `description`: String (derived from the *AgentDoG 1.5* paper's definition for the category)
-   `centroid_embedding`: Array[float] (384 dimensions for `all-MiniLM-L6-v2`)

### DriftResult
The output of the drift scoring process.
-   `log_id`: UUID
-   `drift_score`: Float (cosine distance, 0.0 to 2.0)
-   `review_flag`: Boolean (True if `drift_score` > threshold or text is empty)
-   `closest_category`: String (the taxonomy category with the minimum distance)
-   `distance_to_closest`: Float

### Annotation
Human-in-the-loop validation data.
-   `log_id`: UUID
-   `label`: String ("Attack", "Benign", "Ambiguous")
-   `annotator_id`: String
-   `drift_score_blind`: Float (False, not shown to annotator)

## 2. Relationships

-   **Log** (1) --> (N) **DriftResult** (One log produces one result)
-   **Taxonomy** (1) --> (N) **DriftResult** (Each result references a closest category)
-   **Log** (1) --> (N) **Annotation** (One log may be annotated by multiple people)

## 3. Constraints & Rules

-   **Empty Logs**: If `text` is empty/whitespace, `drift_score` = 2.0 (max distance), `review_flag` = True.
-   **Missing Data**: If `Taxonomy` is empty, the system raises a `ValueError` with code `E_TAXONOMY_MISSING`.
-   **Missing Timestamp**: If source lacks timestamp, derive from `log_id` hash (SHA256) to ensure reproducibility.
-   **Memory**: Batch processing must not exceed `MAX_RAM_GB=7`.
-   **Reproducibility**: All `log_id`s must be deterministic (e.g., `uuid5(namespace, id_string)`). No random UUIDs.

## 4. Derived Metrics

-   **Drift Score**: `1.0 - cosine_similarity(log_embedding, closest_centroid)`
    -   Range: [0.0, 2.0] (since cosine similarity is [-1, 1], distance is [0, 2]).
    -   *Note*: Standard cosine distance is `1 - similarity`.
-   **Cohen's d**: Effect size between benign and attack drift scores.
-   **Cohen's Kappa**: Inter-annotator agreement.
