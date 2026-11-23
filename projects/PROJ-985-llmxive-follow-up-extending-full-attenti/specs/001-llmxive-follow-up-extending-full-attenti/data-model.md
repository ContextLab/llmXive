# Data Model: llmXive Follow-up: Extending "Full Attention Strikes Back"

## Entities

### TokenUnit
Represents a single token in the corpus with computed features and ground truth labels.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sequence_id` | String | Unique identifier for the source document. | Non-null |
| `token_index` | Integer | Position of the token within the sequence. | 0 <= index < sequence_length |
| `text` | String | The token text. | Non-null |
| `position` | Float | Normalized position (0.0 to 1.0). | 0.0 <= position <= 1.0 |
| `entropy` | Float | Shannon entropy of the token distribution. | >= 0.0 |
| `pos_tag` | String | Part-of-Speech tag (e.g., "NOUN", "VERB"). | Valid spaCy tag or "UNK" |
| `local_perplexity` | Float | Local semantic density metric (computed via **KenLM**). | >= 0.0 |
| `is_rtpurbo_selected` | Boolean | Ground truth: selected by RTPurbo. | True/False |
| `predicted_retrieval` | Boolean | Prediction by the static heuristic. | True/False |
| `target_model` | String | Name of the model used for evaluation (e.g., "Llama-3-8B", "Gemma-2-9B"). | Non-null |

### AttentionMap
Represents the full attention weights for a sequence (intermediate artifact).

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sequence_id` | String | Unique identifier for the source document. | Non-null |
| `attention_weights` | List[Float] | Full attention matrix or selected weights. | Non-null |
| `rtpurbo_indices` | List[Integer] | Indices of tokens selected by RTPurbo. | Non-null, unique |

### StaticHeuristic
The derived rule set for token selection.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `rule_id` | String | Unique identifier for the rule set. | Non-null |
| `entropy_threshold` | Float | Minimum entropy required. | >= 0.0 |
| `pos_list` | List[String] | List of allowed POS tags. | Non-null |
| `position_min` | Float | Minimum position (optional). | 0.0 <= value <= 1.0 |
| `position_max` | Float | Maximum position (optional). | 0.0 <= value <= 1.0 |
| `derived_from_model` | String | Model used to derive the rules (e.g., "Llama-3-8B"). | Non-null |

### EvaluationMetric
Structured record of performance metrics.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `method` | String | "Full", "Learned", "Static", or "Static_CrossModel". | Non-null |
| `perplexity` | Float | Perplexity score. | > 0.0 |
| `exact_match` | Float | Exact match accuracy. | 0.0 <= value <= 1.0 |
| `seed` | Integer | Random seed used (for Static mean). | Non-null |
| `p_value` | Float | Statistical significance p-value. | 0.0 <= value <= 1.0 |
| `model` | String | Target model for evaluation (e.g., "Llama-3-8B", "Gemma-2-9B"). | Non-null |

## Data Flow

1.  **Input**: RULER documents (streamed, sampled subset).
2.  **Processing**:
    -   `extract_ground_truth.py`: Generates `AttentionMap` artifacts (Llama-3-8B).
    -   `compute_features.py`: Generates `TokenUnit` records with features (KenLM, spaCy).
    -   `merge_dataset.py`: Joins features and labels into a single `TokenUnit` dataset.
3.  **Training**: `train_static.py` consumes `TokenUnit` dataset to produce `StaticHeuristic` (5 seeds).
4.  **Evaluation**:
    -   `run_baselines.py`: Consumes `StaticHeuristic` and `TokenUnit` dataset to produce `EvaluationMetric` records (Llama-3-8B).
    -   `cross_model_eval.py`: Consumes `StaticHeuristic` and new `AttentionMap` (Gemma-2-9B) to produce `EvaluationMetric` records (Cross-Model).
5.  **Output**: Final metrics and statistical analysis report.

## Storage Strategy

-   **Raw Data**: RULER dataset streamed from HF Hub (no local storage required unless cached).
-   **Intermediate Data**: `AttentionMap` artifacts stored temporarily in `data/intermediate/` and deleted after feature computation.
-   **Derived Data**: `TokenUnit` dataset stored as Parquet in `data/derived/` with checksums.
-   **Models**: `StaticHeuristic` rules stored as JSON in `data/models/`.
-   **Results**: `EvaluationMetric` records stored as CSV in `data/results/`.