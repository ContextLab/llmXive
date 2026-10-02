# Quickstart Guide

## Prerequisites
- Python 3.9+
- `pip install -r code/requirements.txt`

## Execution
Run the full pipeline end-to-end:

```bash
python code/main.py
```

Or run individual steps manually:

### 1. Download Data
```bash
python code/data/download.py --sample-size 1000
```

### 2. Verify Checksums
```bash
python code/data/verify_checksum.py
```

### 3. Extract Geometry
```bash
python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl
```

### 4. Run Solver
```bash
python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl --latency-log data/derived/latency_log.jsonl --exclusion-log data/derived/solver_failures.json
```

### 5. Generate Benchmark Results
```bash
python code/benchmark/generate_benchmark_results.py --predictions data/derived/predictions.jsonl --vlm data/derived/vlm_baseline.csv --ground-truth data/derived/ground_truth.csv --latency data/derived/latency_log.jsonl --output data/results/benchmark_results.csv
```

### 6. Sensitivity Analysis
```bash
python code/benchmark/sensitivity.py --input data/results/benchmark_results.csv --output data/results/sensitivity_analysis.csv
```

### 7. Analyze Failures
```bash
python code/benchmark/analyze_failures.py --results data/results/benchmark_results.csv --output data/derived/failure_classification.json
```

### 8. Generate Failure Report
```bash
python code/benchmark/generate_failure_report.py --results data/results/benchmark_results.csv --classification data/derived/failure_classification.json --output data/results/failure_analysis_report.md
```

### 9. Generate Final Report
```bash
python code/validate/final_report_generator.py
```

## Results
Key outputs are located in `data/results/`:
- `benchmark_results.csv`
- `sensitivity_analysis.csv`
- `failure_analysis_report.md`
- `final_research_report.md`