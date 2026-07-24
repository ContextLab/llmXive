# Quickstart Guide: llmXive - SWE-Explore Follow-up

This guide provides the steps to set up and run the llmXive automated science pipeline for the SWE-Explore follow-up project.

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- Git (for version control)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Create project structure** (if not already done):
 ```bash
 python code/setup_project_structure.py
 ```

## Execution Workflow

The pipeline consists of several sequential stages. Run them in order:

### 1. Data Download
```bash
python code/data/download.py
```
Downloads the SWE-Explore dataset from HuggingFace.
Output: `data/raw/bench.final.public.jsonl`

### 2. Ground Truth Derivation
```bash
python code/data/derive_gt.py
```
Parses solution patches to derive ground truth line numbers.
Output: `data/raw/bench.final.public.gt.jsonl`

### 3. Data Curation (Hard Subset & Synthetic Issues)
```bash
python code/data/curate.py
```
Filters hard instances, generates synthetic issues, and creates metadata.
Outputs:
- `data/curated/hard_subset.jsonl`
- `data/curated/non_hard_subset.jsonl`
- `data/curated/synthetic_issues.jsonl`
- `data/curated/synthetic_issues_meta.json`

### 4. Validation
```bash
python code/data/validate_hard.py
```
Generates a validation report for the hard subset.
Output: `data/curated/validation_report.md`

### 5. Agent Execution (Baseline & Iterative)
```bash
python code/agent/static_baseline.py
python code/agent/iterative.py
```
Runs the static multi-query baseline and iterative agent loop.
Outputs:
- `data/results/baseline_logs.jsonl`
- `data/results/iterative_logs.jsonl`

### 6. Turn-Limit Sweep (Optional)
```bash
python code/agent/sweep_turns.py
```
Executes the iterative agent with varying turn limits.
Output: `data/results/sweep_results.json`

### 7. Metrics & Statistical Analysis
```bash
python code/metrics/coverage.py
python code/metrics/ranking.py
python code/analysis/stats.py
```
Calculates coverage, ranking metrics, and performs statistical tests.
Output: `data/results/final_metrics.json`

### 8. Visualization
```bash
python code/analysis/plots.py
```
Generates plots for coverage and survival curves.
Output: `docs/figures/`

### 9. Report Generation
```bash
python code/analysis/report_generator.py
```
Generates the final research report.
Output: `paper/draft.md`

## Main Execution Script

For a streamlined run (subject to configuration):
```bash
python code/main.py --max-hours 6
```
Note: The `--mode` flag is not supported. Use `--max-hours` to set execution time limits.

## Artifact Verification

After running the full pipeline, verify the existence of key artifacts:
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Missing dependencies**: Ensure `requirements.txt` is installed.
- **Data fetch failures**: The pipeline will fail loudly if the dataset cannot be downloaded. Check network connectivity and HuggingFace availability.
- **Memory errors**: The pipeline uses streaming for large datasets. Ensure sufficient disk space for temporary files.

## Configuration

Edit `code/config.py` to modify:
- Data paths
- Random seeds
- Hard instance percentile threshold
- Validation sample size
- Baseline query count
- Synthetic issue count