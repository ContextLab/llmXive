# Data Gap Protocol

## Overview

This document defines the Data Gap Protocol for the "Predicting the Impact of Composition on the Weibull Modulus of Ceramics" project. The protocol ensures that the pipeline halts gracefully and reports insufficient data before attempting to run modeling tasks that require a minimum dataset size.

## Trigger Condition

The protocol is triggered when the total number of valid entries (`N`) after data ingestion and cleaning is **less than 30**.

## Execution Flow

1. **Data Ingestion**: All data sources (Materials Project, NIST, arXiv, Curated Literature) are fetched and merged.
2. **Data Cleaning**: The `clean_data()` function in `code/ingestion.py` filters for valid stoichiometry and required fields.
3. **Gap Check**: The `validate_data_gap()` function is called with the cleaned dataset.
4. **Decision**:
 - If `N >= 30`: The pipeline proceeds to descriptor computation and modeling.
 - If `N < 30`: The pipeline triggers the Data Gap Protocol.

## Halting Logic

When `N < 30`:
1. The `generate_data_availability_report()` function is called immediately.
2. A JSON report is written to `data/reports/data_availability_report.json`.
3. The pipeline logs: `INFO: PROJECT_HALTED: Insufficient data (N={N})`.
4. The process exits with code `1` (`sys.exit(1)`).
5. No further modeling or analysis tasks are executed.

## Report Schema

The `data/reports/data_availability_report.json` file must contain the following fields:

```json
{
 "total_sources": "<integer>",
 "valid_entries": "<integer>",
 "reason_code": "<string>",
 "timestamp": "<ISO 8601 datetime string>"
}
```

### Field Definitions

- **`total_sources`**: The count of distinct data sources that were successfully fetched and merged.
- **`valid_entries`**: The number of rows in the dataset that passed the cleaning filters (valid stoichiometry, non-null Weibull modulus, etc.).
- **`reason_code`**: A machine-readable code indicating the specific reason for the halt.
 - `DATA_GAP_INSUFFICIENT_ENTRIES`: The primary reason when `N < 30`.
- **`timestamp`**: The UTC timestamp when the report was generated, in ISO 8601 format (e.g., `2023-10-27T10:00:00Z`).

## Implementation Details

The protocol is implemented in `code/ingestion.py`:

- **`validate_data_gap(df)`**: Checks the length of the input DataFrame. If `len(df) < 30`, it calls `generate_data_availability_report()` and exits.
- **`generate_data_availability_report(total_sources, valid_entries)`**: Constructs the JSON object and writes it to `data/reports/data_availability_report.json`.

## Verification

To verify the protocol works correctly:
1. Ensure the pipeline has processed data.
2. If the dataset is small (or if a test file like `data/raw/test_n29.csv` with 29 rows is used), the pipeline should halt.
3. Check that `data/reports/data_availability_report.json` exists and contains valid JSON with the required schema.
4. Confirm the process exit code was `1`.

## Dependencies

- This protocol must be implemented and verified before T047 (Update `docs/data_gap_protocol.md` with exact report generation steps).
- It depends on T017 (Implement `validate_data_gap()`) and T017b (Implement `generate_data_availability_report()`).