# Quickstart Guide: Evaluating LLM-Driven Code Simplification

This guide provides a step-by-step walkthrough to reproduce the research pipeline for evaluating the effectiveness of LLM-driven code simplification on performance.

## Prerequisites

- Python 3.11+
- 500MB+ available RAM (sandbox limits)
- Internet connection (for initial dataset download)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

Ensure the project structure is initialized:

```bash
python code/create_structure.py
python code/configure_linting.py
```

## 2. Data Acquisition & Preprocessing (User Story 1)

This phase downloads the CodeSearchNet dataset, extracts valid Python functions, and creates a stratified sample.

### Download Raw Data
```bash
python code/data/download.py
```
*Output*: `data/raw/codesearchnet-python.parquet`

### Extract & Validate Functions
```bash
python code/data/extract.py
python code/data/validate.py
```
*Output*: `data/processed/validated_functions.jsonl`

### Preprocess & Sample
```bash
python code/data/preprocess.py
python code/data/sample.py
```
*Output*: `data/processed/pilot_sample.jsonl` (50 functions) and `data/processed/validated_functions.jsonl` (200 functions)

## 3. LLM-Driven Simplification (User Story 2)

This phase uses a CPU-quantized model to generate simplified code and verifies functional equivalence.

### Run Simplification Pipeline
```bash
python code/main_simplify.py
```
*Output*: `data/processed/simplified_functions.jsonl`

### Filter Drifted Pairs
```bash
python code/main_filter_drift.py
```
*Output*: `data/processed/valid_pairs.jsonl` (Original, Simplified pairs with verified equivalence)

## 4. Benchmarking & Statistical Analysis (User Story 3)

This phase benchmarks performance and performs statistical significance testing.

### Run Full Benchmark
```bash
python code/main_benchmark.py
```
*Output*: `results/benchmark_results.json` (raw timing data)

### Generate Statistical Summary
```bash
python code/main_statistical_summary.py
```
*Output*: `results/statistical_summary.json` (p-values, significance flags)

### Generate CSV Report
```bash
python code/main_summary.py
```
*Output*: `results/summary.csv` (mean deltas, std, p-values)

## 5. Verification

Verify artifact integrity:
```bash
python code/checksum.py
```

## Troubleshooting

- **Sandbox Timeout**: If functions exceed 5s, they are excluded automatically. Check `logs/pipeline.log` for exclusion reasons.
- **Memory Limit**: The sandbox enforces a 500MB limit. Ensure your environment has sufficient free RAM.
- **Equivalence Drift**: If too many pairs are filtered, review the prompt configuration in `code/models/simplify.py`.

## API Reference

See individual module docstrings for detailed API usage:
- `code/benchmark/runner.py`: Benchmark execution logic.
- `code/benchmark/stats.py`: Statistical testing utilities.
- `code/utils/sandbox.py`: Execution safety wrappers.
