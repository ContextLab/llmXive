# Data Gap Protocol

This document describes the protocol for detecting insufficient data, generating the
Data Availability Report, and halting the pipeline to prevent training on
statistically invalid sample sizes.

## Overview

The pipeline enforces a minimum dataset size of **N >= 30** valid ceramic entries
before proceeding to modeling. This threshold ensures statistical significance for
cross-validation and model evaluation.

If the total number of valid entries (after ingestion, cleaning, and descriptor
computation) is less than 30, the pipeline:
1. Generates a `data/reports/data_availability_report.json`
2. Halts execution with a clear error message
3. Logs the event to `logs/data_gap.log`

## Trigger Conditions

The protocol is triggered when:
- Total valid rows in `data/processed/step4_final.csv` < 30
- OR total valid rows in `data/raw/combined_raw.csv` (pre-cleaning) < 30
- OR after filtering for `sample_count >= 30` per entry, the total row count is < 30

## Report Schema

The `data/reports/data_availability_report.json` file contains:

```json
{
 "status": "HALTED",
 "reason": "Insufficient data: N < 30",
 "timestamp": "ISO-8601 timestamp",
 "data_sources": {
 "materials_project": {
 "raw_count": <int>,
 "valid_count": <int>
 },
 "nist": {
 "raw_count": <int>,
 "valid_count": <int>
 },
 "arxiv": {
 "raw_count": <int>,
 "valid_count": <int>
 },
 "curated_literature": {
 "raw_count": <int>,
 "valid_count": <int>
 }
 },
 "total_valid_entries": <int>,
 "minimum_required": 30,
 "deficit": <int>,
 "recommendations": [
 "Expand data sources",
 "Relax filtering criteria (with caution)",
 "Use transfer learning from related domains"
 ]
}
```

## Implementation Details

### 1. Validation Function

The `validate_data_gap()` function in `code/ingestion.py` performs the check:

```python
def validate_data_gap(input_path: str, min_entries: int = 30) -> bool:
 """
 Validates that the input dataset has at least min_entries rows.
 Returns True if valid, False otherwise.
 """
 df = pd.read_csv(input_path)
 if len(df) < min_entries:
 generate_data_availability_report(len(df), min_entries)
 return False
 return True
```

### 2. Report Generation

The `generate_data_availability_report()` function creates the JSON artifact:

```python
def generate_data_availability_report(current_count: int, min_required: int):
 """
 Generates the data availability report and writes it to disk.
 """
 report = {
 "status": "HALTED",
 "reason": f"Insufficient data: N={current_count} < {min_required}",
 "timestamp": datetime.now().isoformat(),
 "total_valid_entries": current_count,
 "minimum_required": min_required,
 "deficit": min_required - current_count,
 "recommendations": [
 "Expand data sources",
 "Relax filtering criteria (with caution)",
 "Use transfer learning from related domains"
 ]
 }

 output_path = Path("data/reports/data_availability_report.json")
 output_path.parent.mkdir(parents=True, exist_ok=True)

 with open(output_path, "w") as f:
 json.dump(report, f, indent=2)

 logger.error(f"Data gap detected. Report written to {output_path}")
 raise RuntimeError(f"Pipeline halted: Insufficient data ({current_count} < {min_required})")
```

### 3. Pipeline Integration

The validation is integrated into the main pipeline flow:

```python
def main():
 #... data fetching and cleaning steps...

 # Validate data gap
 cleaned_data_path = Path("data/processed/step4_final.csv")
 if not validate_data_gap(str(cleaned_data_path)):
 # validate_data_gap() raises RuntimeError if check fails
 return

 # Proceed to modeling only if validation passes
 run_modeling_pipeline()
```

## Execution Flow

1. **Ingestion Phase**: Data is fetched from all sources and combined into `data/raw/combined_raw.csv`
2. **Cleaning Phase**: Data is cleaned and processed into `data/processed/step4_final.csv`
3. **Validation**: `validate_data_gap()` checks the row count
4. **Decision**:
 - If N >= 30: Pipeline continues to modeling
 - If N < 30: Report is generated, pipeline halts

## Recovery Actions

If the pipeline halts due to data gap:

1. Review `data/reports/data_availability_report.json` for detailed statistics
2. Check `logs/data_gap.log` for source-specific counts
3. Consider:
 - Adding more data sources
 - Adjusting filtering criteria (e.g., lowering sample_count threshold)
 - Using synthetic data augmentation (only for research, not production)
4. Re-run the pipeline after making changes

## Compliance

This protocol satisfies:
- **FR-003**: Minimum dataset size requirement
- **Plan Phase 0, Task 0.2**: Data gap handling
- **Constitution Principle II**: Data quality enforcement

## Related Files

- `code/ingestion.py` - Contains `validate_data_gap()` and `generate_data_availability_report()`
- `data/reports/data_availability_report.json` - Generated report
- `logs/data_gap.log` - Execution logs
- `tasks.md` - Task T017 and T017b implementation details