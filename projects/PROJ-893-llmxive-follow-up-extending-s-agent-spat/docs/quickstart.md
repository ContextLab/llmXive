# Quickstart Guide: llmXive Follow-up (S-Agent Spatial Reasoning)

This guide outlines the steps to execute the full research pipeline for the symbolic spatial reasoning extension of the S-Agent dataset.

## Prerequisites

- Python 3.9+
- `pip install -r code/requirements.txt`

## Execution Steps

1. **Download and Prepare Data**
 Download the S-Agent dataset (stratified sample of 1,000 scenes) and extract geometric constraints.
 ```bash
 python code/data/download.py --sample-size 1000
 python code/data/verify_checksum.py
 python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl
 ```

2. **Validate Data**
 Ensure data integrity and absence of VLM traces.
 ```bash
 python code/validate/dry_run.py
 python code/validate/vlm_trace_auditor.py
 ```

3. **Run Symbolic Solver**
 Execute the CSP solver on the extracted constraints.
 ```bash
 python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl --latency-log data/derived/latency_log.jsonl --exclusion-log data/derived/solver_failures.json
 ```

4. **Generate Benchmark Results**
 Compare symbolic predictions against VLM baseline and ground truth.
 ```bash
 python code/benchmark/generate_benchmark_results.py --predictions data/derived/predictions.jsonl --vlm data/derived/vlm_baseline.csv --ground_truth data/derived/ground_truth.csv --output data/results/benchmark_results.csv
 ```

5. **Run Statistical Analysis**
 Compute McNemar's test for significance.
 ```bash
 python code/benchmark/metrics.py --input data/results/benchmark_results.csv
 ```

6. **Sensitivity Analysis**
 Sweep accuracy thresholds to verify robustness (SC-005).
 ```bash
 python code/benchmark/sensitivity.py --input data/results/benchmark_results.csv --output data/results/sensitivity_analysis.csv
 ```

7. **Failure Analysis**
 Classify failure modes (Geometric vs Semantic).
 ```bash
 python code/benchmark/analyze_failures.py --results data/results/benchmark_results.csv --output data/derived/failure_classification.json
 ```

8. **Final Report Generation**
 Aggregate all results into the final research report.
 ```bash
 python code/validate/final_report_generator.py
 ```

## Output Artifacts

- `data/results/benchmark_results.csv`: Primary comparison metrics.
- `data/results/sensitivity_analysis.csv`: Threshold sweep results.
- `data/results/final_research_report.md`: Complete research findings.
