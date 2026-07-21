# llmXive Quickstart Guide

This guide provides step-by-step instructions to run the llmXive automated science pipeline.

## Prerequisites

- Python 3.8+
- pip package manager
- Access to HuggingFace datasets
- Minimum 7GB RAM

## Installation

1. Clone the repository:
```bash
git clone
cd llmXive
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python code/setup_project_structure.py
```

## Data Download

Download the SWE-Explore benchmark dataset from HuggingFace:

```bash
python code/data/download.py
```

This will fetch `bench.final.public.jsonl` and save it to `data/raw/`.

## Ground Truth Derivation

Parse solution patches to derive ground truth lines:

```bash
python code/data/derive_gt.py
```

This generates ground truth annotations in `data/curated/`.

## Hard Instance Selection

Filter the dataset to select "hard" instances based on initial coverage scores:

```bash
python code/data/curate.py --filter hard
```

This creates `data/curated/hard_subset.jsonl` and `data/curated/non_hard_subset.jsonl`.

## Synthetic Issue Generation

Generate synthetic ambiguous issues from the non-hard subset:

```bash
python code/data/curate.py --generate-synthetic
```

This produces `data/curated/synthetic_issues.jsonl` with up to 50 mutated issues.

## Agent Execution

Run the static multi-query baseline:

```bash
python code/agent/run_baseline.py
```

Run the iterative agent loop:

```bash
python code/agent/iterative.py
```

Both commands read from `data/results/locked_hard_subset.jsonl` and write logs to `data/results/`.

## Metrics Calculation

Calculate coverage and ranking metrics:

```bash
python code/metrics/coverage.py
python code/metrics/ranking.py
```

Run statistical analysis:

```bash
python code/analysis/stats.py
```

This generates `data/results/final_metrics.json` with Wilcoxon signed-rank test results.

## Report Generation

Generate the final research report:

```bash
python code/analysis/report_generator.py
```

This produces `paper/draft.md` with all results and analysis.

## Validation

Validate the entire pipeline:

```bash
python code/validate_quickstart.py
```

This checks that all required artifacts exist and the pipeline executed successfully.

Expected output:
```
Validation Status: PASSED
Validation Successful
```

The validation log will be saved to `data/validation/quickstart_run.log`.

## Troubleshooting

### Missing HuggingFace credentials
If you encounter authentication errors, set your HF token:
```bash
export HF_TOKEN=your_token_here
```

### Memory issues
If you experience OOM errors, reduce the sample size in `code/config.py`:
```python
VALIDATION_SAMPLE_SIZE = 10 # Reduce from default
```

### Slow execution
The pipeline may take several hours to complete. For faster testing, use a smaller sample:
```bash
python code/agent/iterative.py --sample-size 5
```

## Next Steps

After completing the quickstart, you can:
- Customize the agent prompts in `code/agent/prompts.py`
- Adjust the hard instance selection criteria in `code/config.py`
- Add new metrics in `code/metrics/`
- Extend the statistical analysis in `code/analysis/stats.py`