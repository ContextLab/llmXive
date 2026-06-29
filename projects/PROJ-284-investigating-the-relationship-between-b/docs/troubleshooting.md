# Troubleshooting Guide

Common issues and solutions when running the Brain Network Dynamics pipeline.

## 1. Missing HCP Credentials

**Error:** `ValueError: HCP credentials not found.`

**Solution:**
- Ensure `HCP_USERNAME` and `HCP_PASSWORD` are set as environment variables.
- Or, create a `.env` file in the project root with:
 ```
 HCP_USERNAME=your_username
 HCP_PASSWORD=your_password
 ```

## 2. FSL/AFNI Not Found

**Error:** `FileNotFoundError: FSL tool 'mcflirt' not found.`

**Solution:**
- Install FSL and AFNI and ensure they are in your system PATH.
- If you do not have FSL/AFNI installed, the pipeline will automatically switch to synthetic validation mode on CI. For local runs, you can skip preprocessing steps by setting `SKIP_PREPROCESSING=True` in `code/config.py` (for testing only).

## 3. Memory Errors

**Error:** `MemoryError` or `OOM (Out of Memory)`.

**Solution:**
- Reduce the `BATCH_SIZE` in `code/config.py`.
- Increase the `MEMORY_LIMIT` if your system has more RAM available.
- Close other memory-intensive applications.

## 4. API Rate Limiting

**Error:** `429 Too Many Requests`.

**Solution:**
- The pipeline includes built-in retry logic with exponential backoff. If this error persists, wait a few minutes before retrying.
- Check your HCP account for any rate limit restrictions.

## 5. Correlation Results Empty

**Error:** `No significant correlations found.`

**Solution:**
- This may indicate that there are no significant relationships in the current dataset.
- Check the `data/analysis/correlation_results.csv` for raw p-values (before FDR correction).
- Ensure that the input data (behavioral scores, network metrics) is valid and not all zeros.

## 6. Report Generation Failed

**Error:** `TemplateError: Missing variable 'correlation_table'`.

**Solution:**
- Ensure that the correlation analysis (T024) and report generation (T033) are run in sequence.
- Check that `data/analysis/correlation_results.csv` exists and contains data.

## 7. Synthetic Data Validation Fails

**Error:** `Synthetic tSNR below threshold`.

**Solution:**
- This is expected if the synthetic data generation parameters are incorrect.
- Verify that the synthetic data generation logic in `code/data/preprocess.py` is producing valid NIfTI files.
- Check the `logs/pipeline.log` for detailed error messages.

## 8. Import Errors

**Error:** `ModuleNotFoundError: No module named '...'`.

**Solution:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`.
- Verify that you are running the script from the project root.
- Check that you are using Python 3.11 or higher.
