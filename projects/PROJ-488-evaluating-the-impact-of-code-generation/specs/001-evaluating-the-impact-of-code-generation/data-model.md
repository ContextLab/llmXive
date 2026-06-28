# Data Model: 001-code-review-quality

## Key Entities

### Code Snippet
A single function/method from either dataset.
- **ID**: Unique identifier (string).
- **Source**: Dataset name (string).
- **Repository**: Source repository identifier (string) - added for independence assumption handling.
- **Content**: Code text (string).
- **Length**: Character count (integer).
- **Language**: Programming language (string, e.g., "python").
- **Group**: Origin label (string, e.g., "human", "llm").

### Metric Score
A numeric value representing complexity or bug potential.
- **Snippet ID**: Reference to Code Snippet (string).
- **Metric Type**: Type of metric (string). **Enumerated values**: `cyclomatic_complexity`, `potential_bug_count`, `style_inconsistency`.
- **Score Value**: Numeric score (float).
- **Extraction Timestamp**: ISO 8601 datetime.

### Dataset Group
A collection of snippets labeled by origin.
- **Group Label**: "human" or "llm".
- **Snippet Count**: Number of snippets (integer).
- **Metric Distributions**: Mean, median, variance per metric type (object).

## Data Flow

1. **Raw Data**: Downloaded datasets stored in `data/raw/`.
2. **Processed Data**: Filtered snippets stored in `data/processed/`.
3. **Metrics**: Extracted scores stored in `data/metrics/`.
4. **Results**: Statistical outputs stored in `results/`.

## Schema References

- **Input Schema**: Defined in `contracts/input_dataset.schema.yaml` (raw dataset structure from HF).
- **Output Schema**: Defined in `contracts/metrics_output.schema.yaml`.