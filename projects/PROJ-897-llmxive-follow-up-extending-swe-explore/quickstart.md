# Quickstart Guide: llmXive Pipeline

This guide provides step-by-step instructions to run the llmXive automated science pipeline.

## Prerequisites

- Python 3.9+
- pip
- Git

## Setup

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure the project structure is created:

```bash
python code/setup_project_structure.py
```

## Data Curation (Phase 3)

### Step 1: Download Dataset

```bash
python code/data/download.py
```

This downloads the SWE-bench dataset from HuggingFace and saves it to `data/raw/swe_explore_raw.jsonl`.

### Step 2: Derive Ground Truth

```bash
python code/data/derive_gt.py
```

This parses solution patches and derives ground truth lines, saving to `data/raw/swe_explore_with_gt.jsonl`.

### Step 3: Filter Hard Subset

```bash
python code/data/filter_hard.py
```

This filters instances based on `initial_coverage` scores (Spec FR-001) and saves to `data/curated/hard_subset.jsonl`.

### Step 4: Filter Non-Hard Subset

```bash
python code/data/filter_non_hard.py
```

This creates the complement of the hard subset, saving to `data/curated/non_hard_subset.jsonl`.

### Step 5: Generate Synthetic Issues

```bash
python code/data/mutate.py
```

This generates synthetic ambiguous issues and saves to `data/curated/synthetic_issues.jsonl` and `data/curated/synthetic_issues_meta.json`.

### Step 6: Validate Hard Subset

```bash
python code/data/validate_hard.py
```

This validates the hard subset and generates `data/curated/validation_report.md` and `data/curated/validation_status.json`.

## Agent Execution (Phase 4)

### Step 7: Run Baseline

```bash
python code/agent/static_baseline.py
```

This runs parallel queries per issue and saves to `data/results/baseline_logs.jsonl`.

### Step 8: Run Iterative Agent

```bash
python code/agent/iterative.py
```

This runs the iterative agent loop and saves to `data/results/iterative_logs.jsonl`.

## Analysis (Phase 5)

### Step 9: Run Statistical Analysis

```bash
python code/analysis/stats.py
```

This runs Wilcoxon and Permutation tests and saves to `data/results/stats_summary.json`.

### Step 10: Generate Plots

```bash
python code/analysis/plots.py
```

This generates visualizations in `figures/`.

### Step 11: Generate Report

```bash
python code/analysis/report_generator.py
```

This generates the draft report in `paper/draft.md`.

## Full Pipeline

To run the entire pipeline:

```bash
python code/main.py --max-hours 6
```

## Validation

To validate the quickstart:

```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **ModuleNotFoundError**: Ensure all dependencies are installed (`pip install -r requirements.txt`).
- **File not found**: Ensure previous steps have completed successfully.
- **OOM errors**: The pipeline uses streaming to prevent OOM; if issues persist, check system resources.