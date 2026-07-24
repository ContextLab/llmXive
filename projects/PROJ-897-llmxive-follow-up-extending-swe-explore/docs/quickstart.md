# Quickstart Guide

## Project Structure

This project follows the llmXive automated science pipeline structure:

- `code/`: Source code for data processing, agent execution, and analysis
- `data/raw/`: Raw downloaded datasets
- `data/curated/`: Curated and processed datasets
- `data/results/`: Agent execution results and metrics
- `tests/unit/`: Unit tests
- `tests/contract/`: Contract tests for data schemas
- `contracts/`: Data schema definitions
- `docs/`: Documentation
- `paper/`: Research paper drafts
- `figures/`: Generated plots and figures

## Setup

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Create project structure (if not already created):
 ```bash
 python code/setup_project_structure.py
 ```

3. Configure linting and formatting:
 ```bash
 python code/setup_linting.py
 ```

## Execution Pipeline

The full pipeline runs the following steps in order:

### Step 1: Download Data
```bash
python code/data/download.py
```
Downloads the SWE-Explore benchmark dataset from HuggingFace.

### Step 2: Derive Ground Truth
```bash
python code/data/derive_gt.py
```
Parses solution patches to derive ground truth line references.

### Step 3: Curate Dataset
```bash
python code/data/curate.py
```
Filters hard instances, generates synthetic issues, and creates validation reports.

### Step 4: Validate Hard Subset
```bash
python code/data/validate_hard.py
```
Generates validation report for the hard subset.

### Step 5: Run Baseline Agent
```bash
python code/agent/static_baseline.py
```
Executes static multi-query baseline on hard subset.

### Step 6: Run Iterative Agent
```bash
python code/agent/static_baseline.py
python code/agent/iterative.py
```
Executes iterative agent loop on hard subset.

### Step 7: Run Turn-Limit Sweep
```bash
python code/agent/sweep_turns.py
```
Executes turn-limit sweep analysis.

### Step 8: Compute Metrics
```bash
python code/metrics/coverage.py
python code/metrics/ranking.py
```
Calculates coverage and ranking metrics.

### Step 9: Statistical Analysis
```bash
python code/analysis/stats.py
```
Performs statistical testing (Wilcoxon, Permutation, or Survival Analysis).

### Step 10: Generate Plots
```bash
python code/analysis/plots.py
```
Generates visualization figures.

### Step 11: Generate Final Metrics
```bash
python code/analysis/generate_final_metrics.py
```
Aggregates all metrics and applies Bonferroni correction.

### Step 12: Generate Report
```bash
python code/analysis/report_generator.py
```
Generates the research paper draft.

## Hashing Artifacts

To hash all curated and result artifacts:
```bash
python code/analysis/run_hash_pipeline.py
```

For a streamlined run (subject to configuration):
```bash
python code/main.py --max-hours 6
```
Note: The `--mode` flag is not supported. Use `--max-hours` to set execution time limits.

To validate the quickstart pipeline:
```bash
python code/validate_quickstart.py
```

## Linting and Formatting

Run linter:
```bash
ruff check code/
flake8 code/
```

Format code:
```bash
black code/
```

## Data Flow Diagram

```
Raw Data (HuggingFace)
 ↓
download.py
 ↓
data/raw/bench.final.public.jsonl
 ↓
derive_gt.py
 ↓
data/raw/swe_explore_with_gt.jsonl
 ↓
curate.py (filter_hard.py)
 ↓
data/curated/hard_subset.jsonl
 ↓
validate_hard.py
 ↓
data/curated/validation_report.md
 ↓
static_baseline.py & iterative.py
 ↓
data/results/baseline_logs.jsonl
data/results/iterative_logs.jsonl
 ↓
metrics/coverage.py & metrics/ranking.py
 ↓
data/results/metrics.csv
 ↓
analysis/stats.py
 ↓
data/results/stats_summary.json
 ↓
analysis/generate_final_metrics.py
 ↓
data/results/final_metrics.json
 ↓
analysis/report_generator.py
 ↓
paper/draft.md
```