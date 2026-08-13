# Data Gap Protocol

This document defines the protocol for detecting, reporting, and handling insufficient data scenarios in the `PROJ-314` pipeline.
The protocol ensures that the pipeline halts gracefully when the statistical power of the dataset is insufficient to meet the research requirements (e.g., Minimum N >= 30 for valid Weibull analysis).

## 1. Trigger Conditions

The Data Gap Protocol is triggered during the **Ingestion Phase** (specifically Task T017b) if the following condition is met:

$$ \text{Total Valid Rows} < N_{\text{min}} $$

Where:
- `Total Valid Rows` is the count of rows in `data/processed/step_final_cleaned.csv` after applying the sample count filter (T017a).
- $N_{\text{min}}$ is the minimum required sample size, defined as **30** (per SC-004).

## 2. Protocol Execution Steps

When the trigger condition is met, the pipeline executes the following steps in order:

1. **Generate Report**: Invoke `generate_data_availability_report()` to create `data/reports/data_availability_report.json`.
 - The report must contain the current row count, the required threshold, the specific missing count, and a timestamp.
2. **Log Halting Event**: Write a critical log entry to `logs/ingestion.log` indicating the data gap.
3. **Output Warning**: Print the exact string `Power Limitation: Insufficient data (N < 30)` to **stderr**.
4. **Trigger Final Report**: If the pipeline architecture supports it, ensure `generate_final_report()` is called to capture the failure state in the final output.
5. **Halt Execution**: Exit the main pipeline process with **exit code 1**.

## 3. Data Availability Report Schema

The file `data/reports/data_availability_report.json` must strictly adhere to the following JSON schema:

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Data Availability Report",
 "description": "Report generated when the dataset fails to meet minimum sample size requirements.",
 "type": "object",
 "required": [
 "status",
 "threshold",
 "actual_count",
 "missing_count",
 "timestamp",
 "message"
 ],
 "properties": {
 "status": {
 "type": "string",
 "const": "INSUFFICIENT_DATA",
 "description": "Fixed status indicator for this failure mode."
 },
 "threshold": {
 "type": "integer",
 "minimum": 1,
 "description": "The minimum required sample count (N >= 30)."
 },
 "actual_count": {
 "type": "integer",
 "minimum": 0,
 "description": "The number of valid rows found after cleaning and filtering."
 },
 "missing_count": {
 "type": "integer",
 "minimum": 1,
 "description": "Calculated as threshold - actual_count."
 },
 "timestamp": {
 "type": "string",
 "format": "date-time",
 "description": "ISO 8601 timestamp of when the report was generated."
 },
 "message": {
 "type": "string",
 "description": "Human-readable explanation of the failure."
 },
 "next_steps": {
 "type": "array",
 "items": {
 "type": "string"
 },
 "description": "Recommended actions to resolve the data gap."
 }
 }
}
```

### Example Report Content

```json
{
 "status": "INSUFFICIENT_DATA",
 "threshold": 30,
 "actual_count": 12,
 "missing_count": 18,
 "timestamp": "2023-10-27T10:00:00Z",
 "message": "Data gap detected: Only 12 valid entries found. Minimum required is 30.",
 "next_steps": [
 "Expand data sources (e.g., include more literature sources).",
 "Relax filtering criteria (e.g., lower N threshold if scientifically justified).",
 "Wait for new data ingestion."
 ]
}
```

## 4. Integration with Pipeline

The protocol is integrated into `code/ingestion.py` within the `main` function or the `validate_data_gap` helper.

**Pseudocode Logic:**

```python
def validate_data_gap(df: pd.DataFrame) -> None:
 count = len(df)
 if count < 30:
 report = {
 "status": "INSUFFICIENT_DATA",
 "threshold": 30,
 "actual_count": count,
 "missing_count": 30 - count,
 "timestamp": datetime.now().isoformat(),
 "message": f"Data gap detected: {count} < 30",
 "next_steps": ["Expand sources", "Relax filters"]
 }
 # Write report
 Path("data/reports").mkdir(parents=True, exist_ok=True)
 with open("data/reports/data_availability_report.json", "w") as f:
 json.dump(report, f, indent=2)

 # Log and Halt
 logger.critical("Data gap detected. Halting pipeline.")
 print("Power Limitation: Insufficient data (N < 30)", file=sys.stderr)
 sys.exit(1)
```

## 5. Verification

To verify this protocol works correctly:
1. Create a test dataset `data/raw/test_n.csv` containing exactly **29** valid rows (Task T017c).
2. Run the ingestion pipeline.
3. Assert that the process exits with code 1.
4. Assert that `data/reports/data_availability_report.json` exists and contains valid JSON matching the schema above.
5. Assert that `stderr` contains the string `Power Limitation: Insufficient data (N < 30)`.