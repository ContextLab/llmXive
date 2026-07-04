# Data Model: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

## Entities

### 1. TimeSeriesRecord
Represents a single day's aggregated value for a specific metric.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `date` | `date` (ISO8601) | The date of the observation. | Unique, sorted ascending. |
| `value` | `float` | The metric value (sentiment or search volume). | Not null after imputation. |
| `source` | `string` | Identifier of the data source. | Enum: "GDELT_AVGTONE", "GOOGLE_TRENDS" |
| `metric_name` | `string` | Specific metric name. | e.g., "AVGTONE", "anticipatory_anxiety" |

### 2. AnalysisResult
Represents the output of a statistical test.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `metric` | `string` | Test type (e.g., "Pearson", "Granger"). | |
| `coefficient` | `float` | Correlation coefficient or F-statistic. | |
| `p_value` | `float` | P-value of the test. | 0.0 ≤ value ≤ 1.0 |
| `lag` | `integer` | Lag used (0 for correlation, 1-3 for Granger). | ≥ 0 |
| `significance_flag` | `boolean` | True if p < threshold (0.0167). | |
| `test_date` | `date` | Date the analysis was run. | |

## Data Flow

1. **Raw Data**: `data/raw/gdelt_sentiment.csv`, `data/raw/trends_anxiety.csv`.
2. **Processed Data**: `data/processed/aligned_timeseries.csv`.
3. **Results**: `output/results/analysis_results.json`, `output/reports/summary.pdf`.

## Transformation Rules

- **Alignment**: Inner join on `date`. Only dates present in both series are kept.
- **Imputation**: Forward-fill (`ffill`) for missing values. Max gap allowed: 3 days.
- **Normalization**: Z-score: $z = (x - \mu) / \sigma$. Applied per series.
- **Outliers**: No removal. Z-score normalization handles scale differences.
