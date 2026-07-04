# Data Model: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## 1. Entity Definitions

### TimeSeriesRecord
Represents a single day's aggregated value for a specific metric.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `date` | `date` | Calendar date (YYYY-MM-DD) | Unique, non-null |
| `value` | `float` | Aggregated metric value (news volume or search index) | Non-negative |
| `source` | `string` | Data source identifier | Enum: ["gdelt", "google_trends"] |

### AnalysisResult
Represents the output of a statistical test.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `metric` | `string` | Test type (e.g., "pearson", "granger", "ecm") | Non-null |
| `coefficient` | `float` | Test statistic value | Non-null |
| `p_value` | `float` | P-value of the test | 0 ≤ p ≤ 1 |
| `lag` | `integer` | Lag window used (for Granger/ECM) | ≥ 1 |
| `significance_flag` | `boolean` | True if p < 0.05 (no Bonferroni) | Non-null |
| `stationarity_status` | `string` | Result of ADF test | Enum: ["stationary", "non-stationary"] |
| `cointegration_status` | `string` | Result of Engle-Granger test | Enum: ["cointegrated", "not_cointegrated", "not_applicable"] |

## 2. Data Flow Diagram

```
[Raw Data] 
   ↓ (Fetch via API)
[Raw CSVs] (gdelt_events.csv, google_trends.csv)
   ↓ (Preprocessing: Alignment, Forward Fill, Cointegration/ECM or Differencing)
[Processed CSV] (aligned_timeseries.csv)
   ↓ (Statistical Analysis: Correlation, Granger (AIC/BIC), Sensitivity)
[Analysis Results] (JSON/CSV)
   ↓ (Report Generation)
[Final Report] (PDF/HTML)
```

## 3. Schema Validation

All data files must conform to the schemas defined in `contracts/`.

- **Input Schemas**: `dataset.schema.yaml` for raw and processed data.
- **Output Schemas**: `output.schema.yaml` for analysis results and report metadata.
- **Implementation**: The `pyyaml` library is used in `preprocess.py` and `analyze.py` to validate data against these schemas at runtime.

## 4. Data Hygiene Rules

- **Checksums**: Every file in `data/raw/` and `data/processed/` must have a checksum recorded in the project state file.
- **Immutability**: Raw data files are never modified; derivations create new files.
- **PII**: No personally identifying information is stored or processed.