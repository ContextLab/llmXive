# Data Model: llmXive follow-up: extending "VideoKR: Towards Knowledge-Intensive Video Understandin"

## 1. Conceptual Model

The data model revolves around the **QuestionRecord** enriched with structural metadata derived from the **KnowledgeGraph**.

### Entities

1.  **QuestionRecord**:
    *   Represents a single QA pair from the VideoKR-SFT dataset.
    *   **Attributes**: `question_id`, `question_text`, `answer_text`, `predicted_correctness` (boolean), `chain_length` (integer, derived), `status` (valid/unresolvable/mapping_failure).

2.  **KnowledgeGraph**:
    *   A static graph structure (nodes = entities, edges = relationships).
    *   **Usage**: Read-only during analysis. Used to compute `chain_length`.
    *   **Not Stored**: The graph itself is not persisted as a primary artifact; only the derived `chain_length` is stored in the dataset.

3.  **ThresholdResult**:
    *   Stores the outcome of the statistical tests.
    *   **Attributes**: `threshold_knot`, `p_value`, `effect_size`, `cliff_magnitude`, `is_significant`, `bias_flag`.

## 2. Physical Schema (CSV/Parquet)

### `data/processed/annotated_questions.csv`

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `question_id` | string | Unique identifier for the question. | Raw Data |
| `question_text` | string | The natural language question. | Raw Data |
| `answer_text` | string | The ground truth answer. | Raw Data |
| `predicted_correctness` | boolean | Whether the model's prediction was correct (1/0). | Raw Data |
| `chain_length` | integer | Shortest path hops (1, 2, 3, ...). | Derived (Graph) |
| `status` | string | "valid", "disconnected", or "mapping_failure". | Derived |

*Note: The `chain_length` column is the critical derived feature. It must be computed strictly from the graph, using entity linking to map question text to graph nodes.*

### `data/processed/threshold_results.json`

A JSON object containing the results of the sensitivity analysis and primary threshold detection.

```json
{
  "primary_threshold": 3,
  "results": [
    {
      "knot": 2,
      "p_value": 0.012,
      "effect_size": -0.15,
      "cliff_magnitude": 0.15,
      "is_significant": true
    },
    {
      "knot": 3,
      "p_value": 0.004,
      "effect_size": -0.32,
      "cliff_magnitude": 0.32,
      "is_significant": true
    },
    {
      "knot": 4,
      "p_value": 0.089,
      "effect_size": -0.10,
      "cliff_magnitude": 0.10,
      "is_significant": false
    }
  ],
  "bias_flag": false,
  "disconnection_rates": {
    "1": 0.01,
    "2": 0.02,
    "3+": 0.15
  }
}
```

## 3. Data Flow

1.  **Raw Data** (`data/raw/`) -> **Ingestion Script** -> **Annotated CSV** (`data/processed/`)
2.  **Annotated CSV** -> **Analysis Scripts** -> **Results JSON** + **Plots**
3.  **Results JSON** -> **Report Generation** -> `paper/`

## 4. Constraints & Validation

*   **Completeness**: Every record in `annotated_questions.csv` must have a `chain_length` or a `status` indicating failure.
*   **Integrity**: `chain_length` must be >= 1 for valid records.
*   **Immutability**: Raw data files in `data/raw/` are never modified. Derivations are new files.
