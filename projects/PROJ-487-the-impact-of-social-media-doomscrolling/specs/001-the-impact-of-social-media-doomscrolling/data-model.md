# Data Model: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Entities

### TimeSeriesRecord

Represents a single day's aggregated value for a specific metric.

| Field | Type | Description |
| :--- | :--- | :--- |
| `date` | `str` (YYYY-MM-DD) | The date of the record. |
| `value` | `float` | The aggregated value (event count or search volume). |
| `source` | `str` | The source of the data ("GDELT" or "Google Trends"). |
| `is_stationary` | `bool` | Flag indicating if the series is stationary after preprocessing. |
| `is_normalized` | `bool` | Flag indicating if the series is z-score normalized. |

### BatchMetadata

Tracks batch file naming and checksums for data hygiene.

| Field | Type | Description |
| :--- | :--- | :--- |
| `batch_id` | `str` | Unique identifier for the batch (e.g., "2020-01"). |
| `file_path` | `str` | Path to the raw batch file. |
| `checksum` | `str` | SHA256 checksum of the file. |
| `start_date` | `str` | Start date of the batch. |
| `end_date` | `str` | End date of the batch. |
| `source_type` | `str` | "S3_Bulk" or "API_Pilot". |

### AnalysisResult

Represents the output of a statistical test.

| Field | Type | Description |
| :--- | :--- | :--- |
| `metric` | `str` | The metric being tested (e.g., "Granger Causality", "Correlation"). |
| `coefficient` | `float` | The test statistic (e.g., correlation coefficient, F-statistic). |
| `p_value` | `float` | The p-value of the test. |
| `lag` | `int` | The lag window used (if applicable). |
| `significance_flag` | `bool` | True if p < 0.01 (Bonferroni) OR p < 0.05 (FDR). |
| `stationarity_status` | `str` | "stationary" or "non-stationary". |
| `variance_stable` | `bool` | True if ARCH-LM test indicates stable variance. |

## Data Flow

1. **Raw Data**: Fetched from GDELT (S3/API) and Google Trends, stored in `data/raw/`.
2. **Batch Metadata**: Recorded in `data/raw/batch_metadata.json` for checksums.
3. **Aligned Data**: Merged and aligned to daily timestamps, stored in `data/processed/aligned_timeseries.csv`.
4. **Stationary Data**: Differenced and normalized, stored in `data/processed/stationary_timeseries.csv`.
5. **Results**: Statistical test results stored in `data/reports/analysis_results.json`.

## Constraints

- **Date Range**: 2020-01-01 to 2023-12-31.
- **Completeness**: ≥ 95% of days must have valid values.
- **Stationarity**: All time series must be stationary (ADF p < 0.05) before analysis.
- **Normalization**: All time series must be z-score normalized before correlation/Granger tests.
- **Predictor**: Primary predictor is **Negative News Impact Score** (Volume * |Tone|). AVGTONE is descriptive only.
- **Variance**: ARCH-LM test must indicate stable variance before Pearson correlation.