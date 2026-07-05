# Troubleshooting Guide

## Common Issues

### Issue: Download fails
**Solution**: Check internet connection. The pipeline has built-in retry logic. If it persists, verify the HuggingFace URL in `config.py`.

### Issue: Memory error
**Solution**: Ensure you have at least 7GB of free RAM. [UNRESOLVED-CLAIM: c_7fb5bb87 — status=not_enough_info] The pipeline uses memory-mapped I/O, but large datasets still require significant memory.

### Issue: Checksum mismatch
**Solution**: Re-run `data_ingestion.py` to re-download the data. If it persists, verify the source URL.

### Issue: Analysis takes too long
**Solution**: The pipeline is optimized for CPU. Ensure no other heavy processes are running. Consider reducing the number of permutations in `config.py` for testing (not recommended for final runs).

### Issue: Threshold not found
**Solution**: Verify that `power_results.csv` contains valid data. If all resolutions have power > 0.80, the threshold may be beyond 480m.

## Logging

Logs are written to `code/logs/`. Check `info.log` for general progress and `error.log` for specific errors.

## Support

For issues not covered here, open an issue on the project repository.
