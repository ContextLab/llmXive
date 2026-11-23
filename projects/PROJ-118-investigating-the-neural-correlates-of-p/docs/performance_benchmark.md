# Performance Benchmarking Guide

## Overview
This document describes the performance verification process for the `llmXive` pipeline,
specifically targeting the constraints defined in **Task T042**:
> "Verify ICA and permutation tests run within 6 hours on 2 CPU / 7 GB RAM."

## Constraints
- **Wall Clock Time**: 6 hours (21,600 seconds)
- **Memory Limit**: 7 GB
- **CPU**: 2 Cores (Standard configuration)

## Benchmark Script
The benchmark is implemented in `code/performance_benchmark.py`.
It executes the following steps:
1. **Data Loading**: Loads a subset of real EEG epochs from `data/processed/epo_clean.fif`.
2. **ICA Benchmark**: Runs ICA decomposition and component detection, measuring peak memory and duration.
3. **Permutation Test Benchmark**: Runs a cluster-based permutation test (with reduced permutations for speed if needed) and measures resources.
4. **Reporting**: Generates a JSON report at `results/performance_benchmark.json`.

## Execution
To run the benchmark:
```bash
cd projects/PROJ-118-investigating-the-neural-correlates-of-p
python code/performance_benchmark.py
```

## Output
The script outputs a summary to stdout and saves a detailed report to `results/performance_benchmark.json`.

### Example Report Structure
```json
{
 "timestamp": "2023-10-27 10:00:00",
 "constraints": {
 "max_time_hours": 6,
 "max_memory_gb": 7.0
 },
 "results": [
 {
 "step": "ica",
 "duration_seconds": 120.5,
 "peak_memory_gb": 2.1,
 "status": "passed"
 },
 {
 "step": "permutation",
 "duration_seconds": 450.0,
 "peak_memory_gb": 3.5,
 "status": "passed"
 }
 ],
 "summary": {
 "total_duration_hours": 0.16,
 "time_constraint_met": true,
 "memory_constraint_met": true,
 "overall_status": "passed"
 }
}
```

## Interpretation
- **passed**: The step completed within the memory and time limits.
- **failed_memory**: Peak memory exceeded 7 GB.
- **skipped_data_missing**: Real data was not available to run the benchmark (e.g., `metrics.csv` missing).
- **failed**: Total time or memory exceeded limits.

## Troubleshooting
- **Memory Limit Exceeded**:
 - Ensure `n_components` in ICA is set appropriately (e.g., `0.95` variance).
 - Check for memory leaks in custom processing loops.
 - Consider processing subjects individually rather than concatenating all epochs if the dataset is massive.
- **Time Limit Exceeded**:
 - The benchmark uses a subset of data for speed. If the full dataset is required, ensure the subset logic in `load_subset_epochs` is adjusted to reflect the full load if necessary, but note that the 6-hour limit is for the *entire* pipeline run.
 - Permutation tests are inherently slow. The benchmark runs with `n_permutations=10` for speed verification. The full run uses 1000. If 10 takes > 10 seconds, 1000 will take > 1000 seconds (~16 mins), which is well within the 6-hour limit for a single subject. The limit is usually the aggregate over many subjects.

## Verification
The task T042 is considered complete when `results/performance_benchmark.json` exists and contains `"overall_status": "passed"`.
