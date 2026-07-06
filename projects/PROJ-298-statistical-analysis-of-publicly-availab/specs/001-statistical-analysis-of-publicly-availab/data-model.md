# Data Model: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Entities & Relationships

### 1. Tag (Key Entity)
- **Description**: A normalized technology topic.
- **Attributes**:
  - `tag_name` (string): Lowercase, trimmed (e.g., "python").
  - `total_frequency` (int): Total count across 2015-2023.
  - `has_sufficient_data` (bool): True if ≥12 months with data.
  - `base_tag` (string): Mapped base tag (e.g., "python" for "python-2.7") to handle semantic drift.

### 2. TimeSeries
- **Description**: Monthly frequency counts for a single tag.
- **Attributes**:
  - `tag_name` (string): FK to Tag.
  - `year` (int): 2015-2023.
  - `month` (int): 1-12.
  - `frequency` (int): Count of posts with this tag in this month.
  - `log_frequency` (float): `log(frequency + 1e-6)`.

### 3. TrendResult
- **Description**: Output of Mann-Kendall test.
- **Attributes**:
  - `tag_name` (string): FK to Tag.
  - `slope` (float): Theil-Sen estimator.
  - `p_value` (float): Adjusted p-value (BH corrected).
  - `classification` (string): "Growth", "Decline", "Stable", "Insufficient Power".
  - `ci_lower` (float): 95% CI lower bound.
  - `ci_upper` (float): 95% CI upper bound.
  - `power_status` (string): "Adequate" or "Low".

### 4. DecompositionResult
- **Description**: Output of time series decomposition (FR-009).
- **Attributes**:
  - `tag_name` (string).
  - `method` (string): "STL" or "HP".
  - `adf_p_value` (float).
  - `seasonality_detected` (bool).
  - `ljung_box_p_value` (float).
  - `residual_independence` (bool).

### 5. CoOccurrenceMatrix
- **Description**: Jaccard similarity between tag pairs.
- **Attributes**:
  - `tag_a` (string).
  - `tag_b` (string).
  - `jaccard_score` (float): 0.0 to 1.0.

### 6. Cluster
- **Description**: Group of related tags.
- **Attributes**:
  - `cluster_id` (int).
  - `members` (list of strings): Tag names.
  - `avg_intra_similarity` (float).
  - `validation_t_test_p_value` (float): Result of the two-sample t-test.
  - `validation_jaccard` (float): Match to SO Survey taxonomy.

## File Formats

### 1. `data/processed/monthly_frequencies.csv`
- **Schema**: `tag_name, year, month, frequency, log_frequency, base_tag`
- **Format**: CSV (UTF-8).

### 2. `artifacts/trend_results.json`
- **Schema**: Array of `TrendResult` objects.
- **Format**: JSON.

### 3. `artifacts/decomposition_results.json`
- **Schema**: Array of `DecompositionResult` objects.
- **Format**: JSON.

### 4. `artifacts/clusters.json`
- **Schema**: Array of `Cluster` objects.
- **Format**: JSON.

### 5. `artifacts/validation_status.json`
- **Schema**: `{ "tag_name": { "status": "Correlated" | "Absent" | "Skipped" }, "correlation": float | null }`
- **Format**: JSON.

## Constraints & Validation

- **Uniqueness**: `(tag_name, year, month)` must be unique in `monthly_frequencies.csv`.
- **Range**: `frequency` ≥ 0. `log_frequency` ≥ -13.8 (approx `log(1e-6)`).
- **Completeness**: Only tags with `has_sufficient_data = true` are included in `trend_results`.
- **Hashing**: All files in `data/` and `artifacts/` must have SHA-256 hashes recorded in `state/`.