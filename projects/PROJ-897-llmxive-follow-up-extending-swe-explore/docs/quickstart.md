# Quickstart Guide

## Prerequisites

Ensure you have Python 3.9+ and pip installed.

## Installation

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. (Optional) Setup linting and formatting:
 ```bash
 python code/setup_linting.py
 ```

## Execution

To run the full pipeline end-to-end:

```bash
python code/main.py --mode full
```

**Note**: The `--mode full` flag triggers the complete workflow:
1. **Download**: Fetches `bench.final.public.jsonl` from HuggingFace.
2. **Derive GT**: Parses solution patches to generate ground truth lines.
3. **Curate**: Filters hard instances (by coverage) and generates synthetic issues.
4. **Validate**: Runs automated validation checks.
5. **Sweep**: Executes agent sweeps with varying turn limits.
6. **Stats**: Performs statistical analysis (Wilcoxon/Permutation).
7. **Metrics**: Aggregates final results.
8. **Plots**: Generates visualization figures.
9. **Hash**: Computes SHA256 hashes for all artifacts.

### Single Stage Execution

You can also run individual stages:

```bash
# Download only
python code/data/download.py

# Derive Ground Truth
python code/data/derive_gt.py

# Curation & Synthesis
python code/data/curate.py

# Validation
python code/data/validate_hard.py

# Turn Limit Sweep
python code/agent/sweep_turns.py

# Statistical Analysis
python code/analysis/stats.py

# Generate Final Metrics
python code/analysis/generate_final_metrics.py

# Generate Plots
python code/analysis/plots.py

# Hash Pipeline
python code/analysis/run_hash_pipeline.py
```

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/raw/swe_explore_raw.jsonl`
- `data/raw/swe_explore_with_gt.jsonl`
- `data/curated/hard_subset.jsonl`
- `data/curated/non_hard_subset.jsonl`
- `data/curated/synthetic_issues.jsonl`
- `data/curated/synthetic_issues_meta.json`
- `data/curated/validation_report.md`
- `data/results/baseline_logs.jsonl`
- `data/results/iterative_logs.jsonl`
- `data/results/sweep_results.json`
- `data/results/final_metrics.json`
- `figures/coverage_histogram.png`
- `figures/ranking_boxplot.png`
- `paper/draft.md`

## Troubleshooting

- **Missing Module**: Ensure `code/requirements.txt` was installed.
- **File Not Found**: Verify that previous stages completed successfully.
- **Memory Error**: The pipeline uses streaming for large datasets; ensure sufficient RAM (>=7GB recommended for model loading).