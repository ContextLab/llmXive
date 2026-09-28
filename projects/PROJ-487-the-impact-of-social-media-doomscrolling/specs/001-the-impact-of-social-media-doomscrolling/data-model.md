# Data Model: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Entity Definitions

### TimeSeriesRecord
Represents a single day's aggregated value for a specific metric.
*   `date`: `YYYY-MM-DD` (String) - The date of the record.
*   `value`: `float` - The aggregated metric value (EventCount or Search Volume).
*   `source`: `string` - Identifier for the data source (e.g., "GDELT", "GoogleTrends").
*   `is_zero_event`: `boolean` - True if the value is explicitly 0 (valid zero), False if interpolated.

### AnalysisResult
Represents the output of a statistical test.
*   `metric`: `string` - Name of the test (e.g., "Pearson", "Granger").
*   `coefficient`: `float` - The calculated coefficient (r or F-stat).
*   `p_value`: `float` - The p-value of the test.
*   `lag`: `integer` - The lag window used (for Granger).
*   `significance_flag`: `boolean` - True if p < alpha (corrected).
*   `stationarity_status`: `string` - "stationary" or "non_stationary".

## Data Flow

1.  **Raw Ingestion**: `fetch_gdelt.py` and `fetch_trends.py` generate `data/raw/news_volume.csv` and `data/raw/anxiety_trends.csv`.
2.  **Preprocessing**: `preprocess_data.py` aligns timestamps, handles missing values, tests stationarity, and outputs `data/processed/aligned_timeseries.csv`.
3.  **Analysis**: `run_analysis.py` consumes the processed file and generates `data/reports/analysis_results.json` and `data/reports/plots/`.

## Schema Contracts

The data model is enforced by the following schemas:
*   `contracts/dataset.schema.yaml`: Validates the structure of the aligned time-series data.
*   `contracts/output.schema.yaml`: Validates the structure of the analysis results.
