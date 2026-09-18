# Troubleshooting Guide

## Common Issues

### Issue: Pipeline halts with "Data Gap: Human-rated ambiguity missing"
**Cause**: Human-rated ambiguity scores are missing.
**Solution**: Obtain human-rated ambiguity scores from a verified source. Do not use synthetic derivation.

### Issue: "Linkage is <90%"
**Cause**: More than 10% of trials cannot be linked to stimuli.
**Solution**: Check `data/primes` and `data/targets` for missing images. Re-run ingestion.

### Issue: LMM model fails to converge
**Cause**: Data may be too noisy or model structure is incorrect.
**Solution**: Check `state/model_convergence_metrics.json` for details. Try alternative optimizers.

### Issue: PII leak detected
**Cause**: Personal information found in data.
**Solution**: Remove PII from source data and re-run the pipeline.

### Issue: "Missing images" warning
**Cause**: Some images are missing in `data/primes` or `data/targets`.
**Solution**: If >10% missing, the pipeline halts. If ≤10% missing, the pipeline proceeds with a warning.

### Issue: Convergence rate < threshold
**Cause**: Model is struggling to converge.
**Solution**: Check data quality. Consider simplifying the model structure.

## Debugging Tips
- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
- Check `state.yaml` for artifact checksums.
- Run `python code/validation/validate_quickstart.py` for full validation.
