# llmXive Memory Optimization Pipeline - Quick Start Guide

## Overview

This guide provides the commands to run the full llmXive memory optimization pipeline,
from data loading through analysis and reporting.

## Prerequisites

- Python 3.10+
- spaCy model: `en_core_web_sm` (install with `python -m spacy download en_core_web_sm`)
- All dependencies from `code/requirements.txt`

## Installation

```bash
cd code
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Pipeline Execution

### Step 1: Data Loading and Graph Generation

Fetch the LoCoMo dataset, extract triples, build graphs, and generate noisy versions:

```bash
python code/data_loader.py
```

This command:
1. Downloads `data/raw/locomo.jsonl`
2. Extracts triples from context
3. Builds clean graphs → `data/intermediate/graphs_raw.json`
4. Injects noise (ratio=0.1, seed=42) → `data/processed/graphs/graph_noise_42.json`

### Step 2: Baseline Execution (Full Strategy)

Run the full traversal strategy on clean graphs:

```bash
python code/runner.py --strategy full --input data/intermediate/graphs_raw.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/baseline_results.csv
```

### Step 3: Heuristic Execution (Lazy Strategy)

Run the lazy traversal strategy on clean graphs:

```bash
python code/runner.py --strategy lazy --input data/intermediate/graphs_raw.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/lazy_results.csv --threshold 0.7
```

### Step 4: Heuristic Execution (Greedy Strategy)

Run the greedy traversal strategy on clean graphs:

```bash
python code/runner.py --strategy greedy --input data/intermediate/graphs_raw.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/greedy_results.csv --topk 5
```

### Step 5: Statistical Analysis

Perform statistical tests comparing strategies:

```bash
python code/analysis/stats.py
python code/analysis/threshold_analysis.py
python code/analysis/correlation_analysis.py
```

### Step 6: Generate Reports

Generate the final analysis report:

```bash
python code/analysis/generate_docs.py
```

## Validation

Run the validation suite to ensure all outputs are correct:

```bash
python code/quickstart_validator.py
```

## Expected Outputs

After running the full pipeline, the following files should exist:

- `data/raw/locomo.jsonl` - Raw dataset
- `data/intermediate/graphs_raw.json` - Clean graphs
- `data/processed/graphs/graph_noise_42.json` - Noisy graphs
- `data/processed/baseline_results.csv` - Full strategy results
- `data/processed/lazy_results.csv` - Lazy strategy results
- `data/processed/greedy_results.csv` - Greedy strategy results
- `data/processed/statistical_results.json` - Statistical test results
- `data/processed/threshold_analysis.json` - Threshold analysis
- `data/processed/correlation_results.json` - Correlation analysis
- `data/results/report.md` - Final report