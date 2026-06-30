# Data Model: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

## Entities

### 1. FluViewSeries
Weekly ILI rates after preprocessing.
- `week_id`: string (ISO week, e.g., "2020-W01")
- `ili_rate`: float (original rate)
- `log_ili`: float (log-transformed rate, with 0s replaced by 0.01)
- `standardized_ili`: float (z-score computed **within** the current window pair, not globally)
- `seasonal_adjusted`: float (optional, log_ili minus 52-week moving average)

### 2. WindowPair
Consecutive windows used for MMD.
- `window_a`: array of `standardized_ili` (size $W$)
- `window_b`: array of `standardized_ili` (size $W$)
- `center_week`: string (week index of the boundary)
- `mmd_stat`: float (computed statistic)
- `p_value`: float (computed p-value)
- `flagged`: boolean (True if $p < \alpha_{adj}$)

### 3. BaselineResult
Detected change points from Pettitt and BOCPD.
- `method`: string ("Pettitt" or "BOCPD")
- `change_week`: string
- `statistic`: float (test statistic or posterior run-length)
- `p_value`: float (if applicable)

### 4. GroundTruthEvent
Independent outbreak intervals.
- `event_name`: string
- `start_week`: string
- `end_week`: string

### 5. EvaluationMetric
Aggregated performance metrics.
- `metric_name`: string (e.g., "precision", "recall")
- `value`: float
- `configuration`: string (e.g., "window=12, bw=median, tolerance=2")
- `tolerance_weeks`: int

## Relationships

- `FluViewSeries` is the input to `WindowPair` generation.
- `WindowPair` results are compared against `GroundTruthEvent` to produce `EvaluationMetric`.
- `BaselineResult` is compared against `WindowPair` flags for comparative analysis.

## Data Flow

1. **Raw**: `fluview_ili.csv` (downloaded)
2. **Processed**: `ili_preprocessed.csv` (log, zero-handling, local standardization)
3. **Intermediate**: `mmd_results.json` (per-window stats)
4. **Intermediate**: `baselines.csv` (change points)
5. **Output**: `flags.csv`, `report.pdf`, `sensitivity.csv`
