# Quickstart Guide: llmXive Follow-up (S-Agent Extension)

## Prerequisites
- Python 3.11+
- `pip install -r code/requirements.txt`

## Execution Steps

### 1. Download Data
Fetch the S-Agent-300K dataset and sample it.
```bash
python code/data/download.py --sample-size 1000
```

### 2. Verify Checksum
Ensure data integrity.
```bash
python code/data/verify_checksum.py
```

### 3. Validate Distribution
Check statistical validity of the sample.
```bash
python code/data/validate_distribution.py
```

### 4. Extract Geometry (T010)
Parse the dataset and extract constraints.
```bash
python code/data/extract_geometry.py
```
*Output*: `data/derived/constraints.jsonl`, `data/results/exclusion_log.json`

### 5. Dry Run Validation (T029)
Validate constraints before solving.
```bash
python code/validate/dry_run.py
```

### 6. VLM Trace Audit (T027)
Ensure no VLM traces in constraint data.
```bash
python code/validate/vlm_trace_auditor.py
```

### 7. Run Solver (T012)
Execute the symbolic CSP solver.
```bash
python code/solver/run_solver.py \
 --input data/derived/constraints.jsonl \
 --output data/derived/predictions.jsonl \
 --latency-log data/derived/latency_log.jsonl \
 --exclusion-log data/results/solver_exclusions.json
```

### 8. Benchmark (T016, T017)
Calculate metrics and statistical significance.
```bash
python code/benchmark/metrics.py
```

### 9. Generate Benchmark Results (T019b)
Create the final benchmark CSV.
```bash
python code/benchmark/generate_benchmark_results.py
```

### 10. Sensitivity Analysis (T030)
Run threshold sensitivity sweep.
```bash
python code/benchmark/sensitivity.py
```

### 11. Failure Analysis (T021)
Analyze symbolic solver failures.
```bash
python code/benchmark/analyze_failures.py
```

### 12. Final Report (T031)
Generate the comprehensive research report.
```bash
python code/validate/final_report_generator.py
```

## Verification
Run the acceptance checker to ensure all scenarios are met.
```bash
python code/verify_acceptance_scenarios.py
```