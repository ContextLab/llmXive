# Troubleshooting Guide

This document addresses common issues encountered during the execution of the DP-FL project.

## Data Issues

### `DataFetchError: Failed to download FEMNIST after 3 attempts`
- **Cause**: Network connectivity issues or Hugging Face API unavailability.
- **Solution**:
 1. Check your internet connection.
 2. Verify Hugging Face status (https://status.huggingface.co/).
 3. Retry the download command.
 4. If using a proxy, ensure `HTTP_PROXY` and `HTTPS_PROXY` are set correctly.

### `FileNotFoundError: data/raw/femnist.parquet not found`
- **Cause**: Download step was skipped or failed.
- **Solution**: Run `python code/data/download.py --dataset femnist` before proceeding to partitioning.

### `ValueError: Shakespeare excluded per plan.md Gap Analysis`
- **Cause**: Attempting to use the Shakespeare dataset.
- **Solution**: Only `femnist` is supported. Update your command to use `--dataset femnist`.

## Training Issues

### `CUDA out of memory`
- **Cause**: Batch size is too large for available GPU memory.
- **Solution**:
 1. Reduce `--batch_size` manually.
 2. Enable dynamic batch sizing (T031): The system automatically reduces batch size by half (min 16) on OOM.

### `RuntimeError: Expected all tensors to be on the same device`
- **Cause**: Mixing CPU and GPU tensors.
- **Solution**: Ensure all data and models are moved to the same device (`cuda` or `cpu`).

### `ZeroDivisionError` in gradient aggregation
- **Cause**: All selected clients have zero samples for the current round.
- **Solution**: This is handled by T019b (skip and log). If frequent, increase `num_clients` or adjust `--alpha`.

## Analysis Issues

### `FileNotFoundError: results/filtered_data.csv not found`
- **Cause**: Aggregation step was skipped.
- **Solution**: Run `python code/analysis/aggregation.py` before running statistical analysis.

### `RuntimeError: Not enough samples for statistical test`
- **Cause**: Too few seeds or filtered runs for t-test.
- **Solution**: The system will automatically switch to Mann-Whitney U and flag `power_reduced`. Ensure at least 3 valid runs per configuration.

### `MatplotlibWarning: Figure size is too large`
- **Cause**: Plot resolution settings are too high.
- **Solution**: Adjust DPI in `code/analysis/plots.py` or reduce figure size.

## Validation Issues

### `ValidationError: Checksum mismatch`
- **Cause**: Corrupted download.
- **Solution**: Delete `data/raw/femnist.parquet` and re-run the download script.

### `ValidationError: Missing partition metadata`
- **Cause**: Partitioning step was skipped.
- **Solution**: Run `python code/data/partition.py` and `python code/data/generate_partition_metadata.py`.

## Performance Issues

### Slow training
- **Cause**: High number of clients or rounds.
- **Solution**: Reduce `--num_rounds` or `--num_clients` for debugging. Use `--is_streaming` for data loading.

### High memory usage
- **Cause**: Large dataset loaded into memory.
- **Solution**: Use `--is_streaming` in download and partitioning steps.

## Dependency Issues

### `ModuleNotFoundError: No module named 'opacus'`
- **Cause**: Dependencies not installed.
- **Solution**: Run `pip install -r requirements.txt`.

### `ImportError: DLL load failed` (Windows)
- **Cause**: Missing Visual C++ Redistributables.
- **Solution**: Install Microsoft Visual C++ Redistributable for Visual Studio.

## Reporting Bugs

If you encounter an issue not listed here, please:
1. Check the `results/validation_report.md` for detailed error logs.
2. Review the `code/` directory for recent changes.
3. Open an issue on the project repository with:
 - Error message
 - Command used
 - Environment details (OS, Python version, GPU/CPU)
 - Relevant log files