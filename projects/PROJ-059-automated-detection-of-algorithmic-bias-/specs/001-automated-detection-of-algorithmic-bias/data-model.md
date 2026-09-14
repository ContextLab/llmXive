# Data Model: Automated Detection of Algorithmic Bias in Public Code Repositories

## Repository

| Field | Type | Description |
|---|---|---|
| `repo_id` | string | Unique identifier for the repository |
| `repo_name` | string | Name of the repository |
| `repo_url` | string | URL of the repository |
| `file_count` | integer | Number of Python files in the repository |

## Textual Artifact

| Field | Type | Description |
|---|---|---|
| `repo_id` | string | Foreign key referencing the Repository |
| `file_path` | string | Path to the file containing the artifact |
| `artifact_type` | string | Type of artifact (e.g., variable_name, comment) |
| `artifact_text` | string | The actual text of the artifact |
| `bias_score` | float | Bias score for the artifact |
| `sentiment_score` | float | Sentiment score for the artifact |

## Correlation Result

| Field | Type | Description |
|---|---|---|
| `repo_id` | string | Foreign key referencing the Repository |
| `correlation_coefficient` | float | Spearman correlation coefficient |
| `p_value` | float | Bonferroni-corrected p-value |
| `significance` | boolean | Whether the correlation is statistically significant |

## Synthetic Data Point

| Field | Type | Description |
|---|---|---|
| `repo_id` | string | Foreign key referencing the Repository |
| `feature_1` | float | First feature |
| `feature_2` | float | Second feature |
| `true_label` | integer | True label |
| `injected_skew_magnitude` | float | Bias magnitude injected |
| `predicted_label` | integer | Predicted label |
| `fairness_disparity` | float | Calculated fairness metric |
