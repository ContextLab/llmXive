# Data Model: Lottery Draw Integrity and Anomaly Detection

## 1. Entity Definitions

### DrawRecord
Represents a single lottery draw event.
- `draw_date`: `date` (ISO 8601)
- `winning_numbers`: `list[int]` (Sorted, unique)
- `jackpot_amount`: `float` (USD, nullable)
- `total_sales`: `float` (USD, nullable)
- `birthday_cluster_ratio`: `float` (0.0 to 1.0) - **REPLACES `draw_uniformity_deviation`**
- `consecutive_pattern_count`: `int` - **NEW METRIC**
- `is_majority_birthday`: `bool` (True if `birthday_cluster_ratio` > 0.5)
- `quick_pick_rate`: `float | null` (Always `null` per FR-003)

### BiasMetric
Represents a specific deviation pattern analysis.
- `metric_type`: `str` (e.g., "birthday_clustering", "consecutive")
- `threshold_value`: `float` (e.g., 0.60)
- `observed_frequency`: `float`
- `expected_frequency`: `float`
- `correlation_coefficient`: `float`

### CorrelationResult
Represents the statistical outcome of a specific analysis run.
- `correlation_coefficient`: `float`
- `p_value`: `float`
- `confidence_interval_lower`: `float`
- `confidence_interval_upper`: `float`
- `n_samples`: `int`
- `control_variable_note`: `str` (e.g., "Quick Pick rate unobservable")
- `bonferroni_adjusted_p`: `float`

## 2. Data Flow

1.  **Raw Input**: CSV (External Source)
    - Columns: `draw_date`, `winning_numbers` (string), `jackpot`, `sales`
2.  **Processed Input**: `data/processed/draws_cleaned.csv`
    - Columns: `draw_date`, `winning_numbers` (list), `jackpot`, `sales`
    - Filtered: Rows with missing `winning_numbers` removed.
3.  **Derived Output**: `data/processed/draws_metrics.csv`
    - Columns: All from `draws_cleaned` + `birthday_cluster_ratio`, `consecutive_pattern_count`, `is_majority_birthday`.
4.  **Analysis Output**: `data/processed/correlation_results.json`
    - JSON object containing `CorrelationResult` and `BiasMetric` arrays.

## 3. Handling Missing Data
- **Missing `total_sales`**: Row is retained for frequency analysis but excluded from sales-dependent correlation checks. A warning is logged.
- **Missing `winning_numbers`**: Row is excluded entirely.
- **Missing `jackpot`**: Row is excluded from correlation analysis.