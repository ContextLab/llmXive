# Quickstart Guide: llmXive - SWE-Explore Follow-up

## Project Overview

This project implements a follow-up study to "SWE-Explore: Benchmarking How Coding Agents Explore Repositories", focusing on:
- Iterative exploration benchmarking
- Hard instance selection based on initial coverage scores
- Synthetic ambiguous issue generation
- CPU-tractable agent execution with 8-bit quantization
- Statistical analysis using Wilcoxon signed-rank and permutation tests

## Prerequisites

- Python 3.10+
- 7GB+ RAM (for 8-bit quantized model execution)
- pip package manager

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd PROJ-897-llmxive-follow-up-extending-swe-explore
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Create project structure (if not already done):
 ```bash
 python code/setup_project_structure.py
 ```

## Execution Flow

The pipeline consists of the following stages:

### Phase 1: Data Download and Ground Truth Derivation

```bash
# Download the SWE-Explore dataset
python code/data/download.py

# Derive ground truth from solution patches
python code/data/derive_gt.py
```

### Phase 2: Data Curation and Hard Instance Selection

```bash
# Filter hard instances based on initial coverage scores
python code/data/filter_hard.py

# Filter non-hard instances (complement of hard subset)
python code/data/filter_non_hard.py

# Generate synthetic ambiguous issues
python code/data/mutate.py

# Validate hard subset and generate report
python code/data/validate_hard.py
```

### Phase 3: Agent Execution

```bash
# Lock the dataset for consistent execution
# (This step is handled internally by the main pipeline)

# Run static multi-query baseline
python code/agent/static_baseline.py

# Run iterative agent loop
python code/agent/iterative.py

# Run turn-limit sweep
python code/agent/sweep_turns.py
```

### Phase 4: Analysis and Reporting

```bash
# Calculate coverage and ranking metrics
python code/metrics/coverage.py
python code/metrics/ranking.py

# Perform statistical testing
python code/analysis/stats.py

# Generate plots
python code/analysis/plots.py

# Generate final metrics with Bonferroni correction
python code/analysis/generate_final_metrics.py

# Generate report draft
python code/analysis/report_generator.py

# Validate report language
python code/analysis/report_validator.py
```

### Full Pipeline Execution

```bash
# Run the complete pipeline (with execution time monitoring)
python code/main.py --max-hours 5.5
```

## Output Artifacts

The pipeline produces the following artifacts:

- `data/raw/swe_explore_raw.jsonl` - Downloaded dataset
- `data/raw/swe_explore_with_gt.jsonl` - Dataset with derived ground truth
- `data/curated/hard_subset.jsonl` - Hard instances (low coverage)
- `data/curated/non_hard_subset.jsonl` - Non-hard instances
- `data/curated/synthetic_issues.jsonl` - Generated synthetic ambiguous issues
- `data/curated/synthetic_issues_meta.json` - Metadata for synthetic issues
- `data/curated/validation_report.md` - Validation report for hard subset
- `data/results/baseline_logs.jsonl` - Static baseline execution logs
- `data/results/iterative_logs.jsonl` - Iterative agent execution logs
- `data/results/sweep_results.json` - Turn-limit sweep results
- `data/results/final_metrics.json` - Final statistical metrics
- `paper/draft.md` - Generated report draft

## Configuration

Configuration parameters are defined in `code/config.py`:
- `HARD_INSTANCE_PERCENTILE`: Percentile threshold for hard instance selection (default: 0.20)
- `MIN_SYNTHETIC_ISSUES`: Minimum number of synthetic issues to generate (default: 10)
- `TIE_THRESHOLD`: Threshold for switching to permutation test (default: 0.10)
- `SWEEP_SAMPLE_SIZE`: Sample size for turn-limit sweep (default: 100)
- `SWEEP_SEED`: Random seed for sweep sampling (default: 42)

## Troubleshooting

- **ModuleNotFoundError**: Ensure all dependencies are installed via `pip install -r code/requirements.txt`
- **Memory errors**: The pipeline uses 8-bit quantization by default to stay within 7GB RAM constraint
- **Data file not found**: Ensure previous pipeline stages have completed successfully
- **CLI argument errors**: Use `python <script>.py --help` to see available arguments
