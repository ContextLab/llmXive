# Data Gap Protocol

## Overview
This document defines the Data Gap Protocol for the "Predicting the Impact of Composition on the Weibull Modulus of Ceramics" project. The protocol ensures statistical validity of the predictive modeling phase by enforcing minimum data requirements before proceeding to model training and evaluation.

## Trigger Conditions
The Data Gap Protocol is triggered when:
1. Data ingestion and cleaning (T018f) completes
2. Sample count filtering (T017a) is applied (N >= 30 per entry)
3. The total number of valid entries is calculated

**Threshold**: If the total number of valid entries < 30, the protocol halts the pipeline.

## Execution Flow

### Step 1: Validation Check
The `validate_data_gap()` function in `code/ingestion.py` performs the following:
- Loads the cleaned dataset from `data/processed/step_final_cleaned.csv`
- Counts total rows after sample count filtering
- Compares against the minimum threshold (N = 30)

### Step 2: Report Generation
If the threshold is not met, `generate_data_availability_report()` is invoked immediately:
- Creates `data/reports/data_availability_report.json`
- Populates the report with schema-defined fields (see below)
- Logs the report path to `logs/ingestion.log`

### Step 3: Pipeline Halting
Upon report generation:
- A "Power Limitation: Insufficient data (N < 30)" message is printed to **stderr**
- The script exits with **exit code 1**
- No further tasks (T026 onwards) are executed

## Schema: `data/reports/data_availability_report.json`

The report MUST conform to the following JSON schema:

```json
{
 "report_type": "data_availability",
 "timestamp": "ISO-8601 timestamp",
 "status": "HALTED_INSUFFICIENT_DATA",
 "statistics": {
 "total_raw_entries": <integer>,
 "valid_entries_after_filtering": <integer>,
 "minimum_required_entries": 30,
 "deficit": <integer>
 },
 "filter_details": {
 "sample_count_filter_applied": true,
 "sample_count_threshold": 30,
 "entries_removed_by_sample_count": <integer>
 },
 "recommendation": "Collect additional data or relax filtering criteria (if scientifically justified).",
 "next_steps": [
 "Review data sources (HuggingFace, NIST, Literature)",
 "Check for data quality issues in ingestion logs",
 "Consider expanding search parameters for literature data"
 ]
}
```

### Field Definitions
- `report_type`: Fixed string "data_availability".
- `timestamp`: ISO-8601 formatted string of when the report was generated.
- `status`: One of "HALTED_INSUFFICIENT_DATA", "PROCEED".
- `statistics.total_raw_entries`: Count of entries before any filtering.
- `statistics.valid_entries_after_filtering`: Count of entries meeting all criteria.
- `statistics.minimum_required_entries`: Hardcoded threshold (30).
- `statistics.deficit`: Difference between required and actual entries.
- `filter_details.sample_count_filter_applied`: Boolean indicating if T017a was run.
- `filter_details.sample_count_threshold`: The integer threshold used.
- `filter_details.entries_removed_by_sample_count`: Count of entries removed by T017a.
- `recommendation`: Human-readable guidance.
- `next_steps`: Array of actionable items for the researcher.

## Halting Logic

The pipeline halts if:
```python
if total_valid_entries < 30:
 generate_data_availability_report()
 print("Power Limitation: Insufficient data (N < 30)", file=sys.stderr)
 sys.exit(1)
```

## Integration Points

- **T017a (Sample Count Filter)**: Provides the filtered dataset for validation.
- **T017b (Data Gap Validation)**: The primary implementation of this protocol.
- **T026 (Model Preparation)**: Blocked until this protocol passes.
- **T043 (Final Report)**: If the pipeline halts, the final report will include a reference to this data gap report.

## Compliance Notes
- This protocol enforces **SC-004** (Statistical Power Requirement).
- Failure to halt when N < 30 is a critical compliance violation.
- The report file must exist on disk before the script exits.
- No synthetic data fallbacks are permitted; the pipeline must fail loudly.