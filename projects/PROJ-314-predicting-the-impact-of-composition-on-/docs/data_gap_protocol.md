# Data Gap Protocol

This document defines the protocol for detecting insufficient data volume, generating the required availability report, and halting the pipeline execution to prevent invalid statistical analysis.

## 1. Trigger Condition

The Data Gap Protocol is triggered during the **Data Ingestion Phase** (User Story 1) after the initial sample count filtering step.

**Logic:**
1. The pipeline executes `filter_valid_sample_count()` (Task T017a) to retain only entries where `sample_count` (N) >= 30.
2. The function `validate_data_gap()` (Task T017b) immediately calculates the total number of rows remaining in the dataset.
3. **Condition:** If `total_row_count` < 30, the protocol is triggered.

*Note: The threshold of 30 is based on statistical power requirements for reliable Weibull modulus estimation and cross-validation stability (SC-004).*

## 2. Protocol Execution Steps

When triggered, the system must perform the following actions in strict order:

### Step 2.1: Generate Data Availability Report
The system calls `generate_data_availability_report()`. This function creates a JSON artifact documenting the state of the dataset.

**Output Path:** `data/reports/data_availability_report.json`

**Schema:**
```json
{
 "timestamp": "ISO 8601 timestamp of generation",
 "status": "INSUFFICIENT_DATA",
 "total_entries_after_filter": <integer>,
 "minimum_required_entries": 30,
 "deficit": <integer>,
 "filter_applied": "sample_count >= 30",
 "sources_checked": [
 "materials-science/ceramic-reliability",
 "nist_data",
 "arxiv_extraction",
 "curated_literature"
 ],
 "recommendation": "Pipeline halted. Data acquisition required before proceeding to modeling."
}
```

### Step 2.2: Log the Event
The system logs the event to the standard pipeline log (configured in `code/__init__.py`).
- **Level:** `CRITICAL`
- **Message:** `Data Gap Detected: {total_entries} entries found. Minimum required: 30. Halting pipeline.`

### Step 2.3: Output to Standard Error
The system must print the following exact string to `stderr` to ensure immediate visibility in CI/CD or terminal outputs:
```text
Power Limitation: Insufficient data (N < 30)
```

### Step 2.4: Halt Execution
The pipeline must terminate immediately.
- **Exit Code:** `1` (Non-zero failure code)
- **Action:** No further tasks (Modeling, Interpretability, Reporting) should be executed.

## 3. Artifact Definition: `data/reports/data_availability_report.json`

This file serves as the audit trail for data insufficiency. It is required for compliance with the research protocol.

| Field | Type | Description |
|:--- |:--- |:--- |
| `timestamp` | string | ISO 8601 formatted time of the check. |
| `status` | string | Literal value `"INSUFFICIENT_DATA"`. |
| `total_entries_after_filter` | integer | The count of rows remaining after `sample_count >= 30` filter. |
| `minimum_required_entries` | integer | Constant `30`. |
| `deficit` | integer | `minimum_required_entries` - `total_entries_after_filter`. |
| `filter_applied` | string | Description of the filter that led to the low count. |
| `sources_checked` | list | List of data sources attempted during ingestion. |
| `recommendation` | string | Human-readable next step. |

## 4. Implementation Details

### 4.1. Code Location
The logic is implemented in `code/ingestion.py`.

### 4.2. Function Signature
```python
def validate_data_gap(df: pd.DataFrame) -> None:
 """
 Checks if the dataframe has sufficient rows.
 If not, generates the report, logs, prints to stderr, and exits.
 """
```

### 4.3. Dependency
This task depends on `T017a` (Sample Count Filtering) being executed first.

## 5. Recovery Procedure

To resume the pipeline after a Data Gap halt:
1. Investigate the `data/reports/data_availability_report.json` to understand the deficit.
2. Expand data sources (e.g., add more literature, increase arXiv search radius).
3. Re-run the ingestion pipeline from the start.
4. Ensure `total_entries_after_filter` >= 30 before the pipeline proceeds to `T018a`.