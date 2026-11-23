# Troubleshooting Guide

## Common Issues

### Data Fetching Errors

**Symptom**: Pipeline fails to download HCP data.

**Possible Causes:**
- No internet connection
- OpenNeuro service unavailable
- Insufficient disk space

**Solutions:**
1. Verify internet connection
2. Check OpenNeuro status
3. Ensure ~14 GB free disk space
4. Manually download data from OpenNeuro if needed

### Memory Errors

**Symptom**: `MemoryError` or process killed during execution.

**Possible Causes:**
- Cohort too large for available RAM
- Inefficient memory usage

**Solutions:**
1. Reduce cohort size
2. Use `code/utils/cpu_optimization.py` functions
3. Enable chunked processing
4. Close other applications
5. Increase system RAM if possible

### Convergence Failures

**Symptom**: K-Means fails to converge for some subjects.

**Possible Causes:**
- Poor data quality
- Extreme sparsity in functional data
- Inappropriate number of clusters

**Solutions:**
1. Check `data/logs/exclusion_log.json` for details
2. Verify data quality in `data/raw/`
3. Consider adjusting `K_MEANS_K` if justified
4. Exclude problematic subjects (automatically logged)

### Tractography Sensitivity Issues

**Symptom**: Correlations vanish at high confidence thresholds.

**Possible Causes:**
- Original findings driven by tractography false-positives
- Low signal-to-noise ratio in structural data

**Solutions:**
1. Review `data/processed/tractography_correlation_sensitivity.csv`
2. Check `final_report.json` for explicit warnings
3. Report findings as "may be influenced by tractography artifacts"
4. Consider alternative structural connectivity methods

### FDR Correction Yields Zero Significant Findings

**Symptom**: All p-values are non-significant after FDR correction.

**Possible Causes:**
- Small sample size
- Weak associations
- Stringent correction

**Solutions:**
1. Check `data/processed/correlation_results.csv` for raw p-values
2. Review `reports/handle_fdr_edge_case.py` for edge case handling
3. Report transparently: "No significant findings after FDR correction"
4. Consider reporting effect sizes even if non-significant

### Associational Language Violations

**Symptom**: Audit tool flags causal language.

**Possible Causes:**
- Accidental use of causal verbs
- Inconsistent terminology

**Solutions:**
1. Run `python code/reports/audit_associational_language.py`
2. Review flagged sections
3. Replace causal terms with associational equivalents
4. See `docs/associational_language_guide.md` for guidance

### Validation Errors

**Symptom**: Report fails schema validation.

**Possible Causes:**
- Missing required fields
- Incorrect data types
- Schema mismatch

**Solutions:**
1. Run `python code/reports/validate_report.py`
2. Check `contracts/output.schema.yaml` for requirements
3. Ensure all sensitivity analyses are included
4. Verify tractography sensitivity section is present

## Performance Issues

### Slow Execution

**Symptom**: Pipeline takes longer than expected.

**Solutions:**
1. Use `code/main_optimized.py` for optimized execution
2. Enable parallel processing where available
3. Reduce cohort size for testing
4. Profile code with `cProfile`

### High CPU Usage

**Symptom**: CPU at 100% for extended periods.

**Solutions:**
1. This is expected for CPU-only processing
2. Ensure `code/utils/cpu_optimization.py` is being used
3. Consider limiting number of cores if system becomes unresponsive

## Logging and Debugging

### Enable Verbose Logging

Add to `code/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Execution Logs

```bash
cat data/logs/execution_log.json
```

### Check Exclusion Log

```bash
cat data/logs/exclusion_log.json
```

## Getting Help

If you encounter issues not covered here:
1. Check the execution logs
2. Review the error message carefully
3. Search existing issues
4. Open a new issue with:
 - Error message
 - Steps to reproduce
 - System information
 - Relevant log excerpts
