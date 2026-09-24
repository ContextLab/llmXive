# Quickstart Guide: llmXive - S-Agent Spatial Reasoning Extension

This guide describes how to run the full pipeline for the `PROJ-893` project, extending the S-Agent spatial reasoning capabilities with a symbolic CSP solver.

## Prerequisites

- Python 3.9+
- Dependencies installed: `pip install -r code/requirements.txt`
- Access to HuggingFace Hub (if downloading datasets)

## Execution Steps

The pipeline is orchestrated by `code/main.py`, but individual steps can be run manually for debugging or partial execution.

### 1. Download and Verify Data

```bash
# Download the S-Agent dataset (n=1000 sample)
python code/data/download.py --sample-size 1000

# Verify checksums
python code/data/verify_checksum.py --manifest data/manifest.json --dir data/raw
```

### 2. Extract Geometry and Constraints

```bash
python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl
```

### 3. Validate Distribution (Gate)

```bash
python code/data/validate_distribution.py
```

### 4. Run Symbolic Solver

```bash
python code/solver/run_solver.py \
 --input data/derived/constraints.jsonl \
 --output data/derived/predictions.jsonl \
 --latency-log data/derived/latency_log.jsonl \
 --exclusion-log data/results/exclusion_log.json
```

### 5. Load Baselines and Ground Truth

```bash
# Load VLM Baseline
python code/data/load_vlm_baseline.py --output data/derived/vlm_baseline.csv

# Load Ground Truth
python code/data/load_ground_truth.py --output data/derived/ground_truth.csv
```

### 6. Generate Benchmark Results (T019b)

This step generates the primary comparison file `data/results/benchmark_results.csv`.

```bash
python code/benchmark/generate_benchmark_results.py \
 --predictions data/derived/predictions.jsonl \
 --vlm-baseline data/derived/vlm_baseline.csv \
 --ground-truth data/derived/ground_truth.csv \
 --latency-log data/derived/latency_log.jsonl \
 --exclusion-log data/results/exclusion_log.json \
 --output data/results/benchmark_results.csv
```

### 7. Statistical Analysis (T017)

```bash
python code/benchmark/metrics.py \
 --input data/results/benchmark_results.csv \
 --output data/results/benchmark_results.csv \
 --add-mcnemar
```

### 8. Failure Analysis (T021)

```bash
python code/benchmark/analyze_failures.py \
 --results data/results/benchmark_results.csv \
 --solver-failures data/derived/solver_failures.json \
 --output data/derived/failure_classification.json
```

### 9. Sensitivity Analysis (T030)

```bash
python code/benchmark/sensitivity.py \
 --input data/results/benchmark_results.csv \
 --output data/results/sensitivity_analysis.csv
```

## Full Pipeline Execution

To run the entire pipeline in one go (with gates):

```bash
python code/main.py
```

## Output Artifacts

- `data/results/benchmark_results.csv`: Primary comparison metrics.
- `data/results/sensitivity_analysis.csv`: Threshold sensitivity sweep.
- `data/results/final_research_report.md`: Aggregated research findings.
