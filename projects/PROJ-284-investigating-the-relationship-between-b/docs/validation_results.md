# Validation Results

This document summarizes the validation tests performed on the pipeline to ensure correctness and reliability.

## 1. Unit Tests

All unit tests in `tests/unit/` passed successfully.

- **Data Fetcher:** Verified that the HCP fetcher returns valid NIfTI objects on success and handles errors gracefully.
- **Metric Extraction:** Confirmed that graph metrics (Modularity, Efficiency, etc.) match synthetic ground truth values.
- **Visualization:** Verified that scatter plots are generated with correct labels, regression lines, and annotations.

**Command:**
```bash
pytest tests/unit/ -v
```

## 2. Integration Tests

Integration tests in `tests/integration/` validated the end-to-end flow on synthetic data.

- **Preprocessing:** Validated tSNR >= 50 and motion < 0.5mm on synthetic NIfTI data (simulating FSL/AFNI output).
- **Correlation Analysis:** Confirmed that correlation coefficients (r) and p-values match expected values for synthetic datasets with known relationships.
- **Report Generation:** Verified that the generated Markdown report includes all required sections (Limitation Statement, Associational Relationship phrasing, correlation tables).

**Command:**
```bash
pytest tests/integration/ -v
```

## 3. CI Validation (T012a)

The Data Availability Switch logic was validated on a CI runner (`ubuntu-latest`) without FSL/AFNI installed.

- **Scenario:** ICA-FIX data not available (simulated).
- **Action:** Pipeline switched to raw data mode and executed validation using synthetic NIfTI data.
- **Result:** Validation passed; no preprocessing errors logged; synthetic outputs written to `data/processed/`.

**Log Snippet:**
```
[INFO] ICA-FIX not available. Switching to raw data mode.
[INFO] Running synthetic validation on CI.
[INFO] Synthetic tSNR: 65.2 (Threshold: 50) - PASS
[INFO] Synthetic Motion: 0.3mm (Threshold: 0.5) - PASS
```

## 4. Performance Validation

- **Memory Usage:** Dynamic batch sizing successfully kept memory usage under the 7GB limit during matrix computation.
- **Execution Time:** Full pipeline execution on a subset of 10 subjects completed within the expected time frame (approx. 15 minutes on standard hardware).

## 5. Data Integrity

- **Checksums:** Verified checksums of downloaded HCP data match expected values.
- **File Formats:** Confirmed all output files (CSV, NIfTI, PNG) are valid and readable by standard tools (pandas, nibabel, matplotlib).

## Conclusion

The pipeline has passed all validation checks. It is ready for production use with real HCP data.
