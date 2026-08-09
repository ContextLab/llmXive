# Data Gap Protocol

## Overview

This document defines the protocol for detecting insufficient data during the ceramic materials ingestion pipeline and the exact steps for generating the data availability report.

**Trigger Condition**: The pipeline halts if the number of valid ceramic entries (N) after fetching and applying per-entry filters is less than 30.

## Protocol Steps

### Step 1: Data Fetching and Initial Filtering

1. Execute `fetch_data()` in `code/ingestion.py` to retrieve raw data from configured sources (Materials Project, NIST, arXiv).
2. Apply per-entry filters defined in `clean_data()`:
 - Filter for `N >= 30` by explicitly extracting sample count from fields named 'N', 'sample_size', or 'n'.
 - Handle range values: Extract midpoint, set `is_range_flag`, store `range_original`.
 - Impute missing processing params (group median -> global median).
 - Handle non-stoichiometric phases: Exclude if the specific class has < 5 samples.
 - Derive `primary_anion_cation_group` from stoichiometry.

### Step 2: Data Gap Validation

1. Call `validate_data_gap()` in `code/ingestion.py` immediately after cleaning.
2. This function calculates `total_valid_entries` (N) from the cleaned dataset.
3. **Check Condition**:
 - **IF N < 30**: Trigger the Data Gap Protocol (Step 3).
 - **IF N >= 30**: Proceed to descriptor computation and modeling.

### Step 3: Report Generation (Triggered on N < 30)

When the condition `N < 30` is met, the system must:

1. **Call Generation Function**: Execute `generate_data_availability_report()` in `code/ingestion.py`.
 - **Input**: The current count of valid entries (`N`) and the list of source attempts.
 - **Logic**:
 - Count the actual number of sources attempted (not hardcoded).
 - Record the reason code (e.g., "INSUFFICIENT_SAMPLES").
 - Capture the current timestamp.
2. **Write Artifact**: Save the report to `data/reports/data_availability_report.json`.
3. **Log Halt**: Log the message `INFO: PROJECT_HALTED: Insufficient data (N={N})` to `logs/ingestion.log`.
4. **Exit**: Terminate the pipeline with exit code 1.

## Output Schema: `data/reports/data_availability_report.json`

The generated JSON file must strictly adhere to the following schema:

```json
{
 "total_sources": <integer>,
 "valid_entries": <integer>,
 "reason_code": <string>,
 "timestamp": <ISO8601_string>
}
```

### Field Definitions

| Field | Type | Description |
|:--- |:--- |:--- |
| `total_sources` | Integer | The actual count of data sources fetched or attempted during the run. Must be dynamic, not hardcoded. |
| `valid_entries` | Integer | The final count of valid ceramic entries (N) after all filtering steps. This is the value that triggered the halt (N < 30). |
| `reason_code` | String | A standardized code indicating the halt reason. Expected value: `"INSUFFICIENT_SAMPLES"`. |
| `timestamp` | String | ISO8601 formatted timestamp (e.g., "2023-10-27T10:00:00Z") indicating when the report was generated. |

## Implementation Reference

The logic for this protocol is implemented in `code/ingestion.py`:

```python
def validate_data_gap(df: pd.DataFrame) -> None:
 """
 Checks if the number of valid entries is >= 30.
 If N < 30, generates the data availability report and halts.
 """
 N = len(df)
 if N < 30:
 generate_data_availability_report(N)
 logger.info(f"PROJECT_HALTED: Insufficient data (N={N})")
 sys.exit(1)

def generate_data_availability_report(valid_count: int) -> None:
 """
 Generates the data availability report JSON.
 """
 # Implementation details:
 # 1. Count actual sources attempted
 # 2. Construct report dict
 # 3. Write to data/reports/data_availability_report.json
 pass
```

## Verification

To verify this protocol:
1. Run the pipeline with a controlled sample dataset containing < 30 valid entries.
2. Confirm `data/reports/data_availability_report.json` is created.
3. Verify the `valid_entries` field matches the actual sample count.
4. Confirm the process exits with code 1.