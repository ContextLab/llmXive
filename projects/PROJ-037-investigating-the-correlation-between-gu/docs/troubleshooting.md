# Troubleshooting Guide

## Common Issues

### 1. Data Download Fails
**Symptom**: `code/ingestion.py` fails to download AGP/OpenHumans data.
**Cause**: Network issues or changed URLs.
**Solution**:
- Check internet connection.
- Verify URLs in `code/ingestion.py`.
- Manually download data and place in `data/raw/`.

### 2. Missing Dependencies
**Symptom**: `ModuleNotFoundError` for `biom-format`, `skbio`, etc.
**Cause**: Dependencies not installed.
**Solution**:
```bash
pip install -r requirements.txt
```

### 3. Virtual Environment Not Activated
**Symptom**: Scripts fail to find modules.
**Cause**: `venv` not activated.
**Solution**:
```bash
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
```

### 4. No Matching Participants
**Symptom**: `WARNING: No matching participants found` in `logs/ingestion.log`.
**Cause**: AGP and OpenHumans IDs do not overlap.
**Solution**:
- Check ID formats in both datasets.
- Proceed with available sample size (pipeline continues).

### 5. Bootstrap Skipped
**Symptom**: `validation_status.json` shows `resampling_skipped: true`.
**Cause**: N < 40.
**Solution**:
- Collect more data or reduce analysis scope.

### 6. Causal Language Detected
**Symptom**: Reviewer flags causal claims in reports.
**Cause**: Accidental use of "causes", "leads to", etc.
**Solution**:
- Search reports for causal terms.
- Replace with "associates with", "correlates with".

### 7. Plot Generation Fails
**Symptom**: `data/outputs/heatmap.png` missing.
**Cause**: `code/viz.py` truncated or data missing.
**Solution**:
- Ensure `code/viz.py` is complete.
- Verify `data/outputs/correlation_results.csv` exists.

### 8. FDR Correction Errors
**Symptom**: `ValueError` in `apply_fdr_correction`.
**Cause**: Invalid p-values (e.g., NaN).
**Solution**:
- Check for missing p-values in results.
- Filter or impute as needed.

## Contact
For issues not covered here, refer to the project's `README.md` or `design.md`.
