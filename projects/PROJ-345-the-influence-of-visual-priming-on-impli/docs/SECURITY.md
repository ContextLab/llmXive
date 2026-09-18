# Security & PII Handling

## PII Scanning
The pipeline includes a PII scanning module (`code/security/pii_scanner.py`) that checks all text and CSV files for personally identifiable information.

## Execution
Run the PII scan before exporting any data:
```bash
python code/main.py --scan-pii
```
- **Output**: `reports/pii_scan.json`
- **Pass Condition**: `{"leaks": []}`

## Data Sanitization
If PII is detected, the system will log the specific fields and halt further processing until the issue is resolved.

## Best Practices
- Never commit raw data with PII to the repository.
- Use anonymized participant IDs in all processed datasets.
- Regularly scan `data/processed/` for accidental PII leakage.
