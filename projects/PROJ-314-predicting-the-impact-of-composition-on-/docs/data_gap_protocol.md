# Data Gap Protocol

This document defines the protocol for handling insufficient data in the "Predicting the Impact of Composition on the Weibull Modulus of Ceramics" project. It ensures that the pipeline halts gracefully when the dataset is too small to support statistically significant modeling, preventing the generation of spurious results.

## 1. Overview

The Data Gap Protocol is triggered when the total number of valid ceramic entries (`N`) after ingestion and cleaning falls below the minimum threshold required for robust machine learning (N < 30).

**Threshold**: `N < 30`

## 2. Trigger Conditions

The protocol activates in `code/ingestion.py` via the `validate_data_gap()` function after the following steps:
1. Data fetching (Materials Project, NIST, arXiv).
2. Data cleaning (`clean_data()`), including:
 - Filtering for `sample_count >= 30`.
 - Handling range values.
 - Imputing missing processing parameters.
 - Excluding non-stoichiometric phases with < 5 samples.
3. Calculation of the total valid entry count (`N`).

## 3. Halting Logic

If `N < 30`:
1. **Generate Report**: Call `generate_data_availability_report()` to create `data/reports/data_availability_report.json`.
2. **Log Event**: Log `INFO: PROJECT_HALTED: Insufficient data (N={N})` to `logs/ingestion.log`.
3. **Exit**: Terminate the pipeline with exit code `1`.
4. **Do Not Proceed**: No modeling, SHAP analysis, or reporting steps will be executed.

If `N >= 30`:
1. Proceed to the modeling phase (User Story 2).

## 4. Report Schema

The report `data/reports/data_availability_report.json` must contain the following fields:

```json
{
 "total_sources": <int>, // Count of distinct data sources attempted (e.g., 3 for MP, NIST, arXiv)
 "valid_entries": <int>, // The actual count N of valid entries found
 "reason_code": <string>, // "INSUFFICIENT_DATA"
 "timestamp": <string>, // ISO 8601 timestamp of the check
 "sources_breakdown": { // Optional: breakdown of entries per source
 "materials_project": <int>,
 "nist": <int>,
 "arxiv": <int>
 },
 "message": <string> // Human-readable explanation
}
```

## 5. Implementation Details

### 5.1. `generate_data_availability_report()`

**Location**: `code/ingestion.py`

**Logic**:
- Counts the number of valid entries in the processed DataFrame.
- Constructs the dictionary according to the schema above.
- Writes the JSON file to `data/reports/data_availability_report.json`.
- Ensures the `data/reports/` directory exists before writing.

### 5.2. `validate_data_gap()`

**Location**: `code/ingestion.py`

**Logic**:
- Calls `generate_data_availability_report()` if `N < 30`.
- Raises a `SystemExit(1)` or returns a flag to halt the main pipeline loop.

## 6. Verification

To verify the protocol:
1. Create a test dataset with `N < 30` (e.g., `data/raw/test_n29.csv` with 29 rows).
2. Run the ingestion pipeline with the `--force-gap-check` flag (or equivalent test harness).
3. Confirm that:
 - `data/reports/data_availability_report.json` is created.
 - The file contains `valid_entries: 29`.
 - The process exits with code 1.
 - No downstream files (e.g., `data/results/model_metrics.json`) are created.

## 7. Recovery

To recover from a data gap:
1. **Expand Sources**: Add new data sources (e.g., additional literature, expanded API queries).
2. **Relax Filters**: Review cleaning criteria (e.g., `N >= 30` filter, non-stoichiometric exclusion) to see if valid data was inadvertently dropped. *Note: Relaxing scientific filters must be documented.*
3. **Re-run**: Execute the pipeline again. The protocol will re-evaluate the new `N`.

## 8. Compliance

This protocol satisfies:
- **Plan Phase 1, Task 1.5**: Documentation of data availability checks.
- **FR-003**: Requirement to validate sample size.
- **Constitution Principle II**: Ensures data integrity by halting on insufficient evidence.