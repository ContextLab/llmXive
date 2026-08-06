# Quickstart Guide

This guide outlines how to run the full evaluation pipeline for project PROJ-527.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`
- HuggingFace Inference API token set in `HF_API_TOKEN` environment variable

## Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire workflow:
1. Fetches the HumanEval dataset.
2. Generates prompt variants of varying complexity.
3. Queries the LLM to generate code.
4. Executes the generated code against unit tests.
5. Performs statistical analysis on the results.

### Full Run

```bash
python code/main.py
```

### Run with a Subset (Sample Size)

To test quickly or run within time limits, specify a sample size:

```bash
python code/main.py --sample-size 10
```

### Skip Data Fetching

If the dataset is already downloaded, you can skip the fetch step:

```bash
python code/main.py --skip-fetch
```

## Output Artifacts

After successful execution, the following files will be available:

- `data/processed/prompt_variants.parquet`: Generated prompts and metadata.
- `data/results/execution_outcomes.csv`: Pass/fail results per complexity level.
- `data/results/analysis_summary.csv`: Statistical test results (LMM, p-values, effect sizes).
- `data/results/sensitivity_analysis.csv`: Sensitivity analysis results.
- `figures/complexity_performance_curve.png`: Visualization of performance vs. complexity.

## Troubleshooting

- **Missing API Token**: Ensure `HF_API_TOKEN` is set in your environment.
- **Timeouts**: If execution times out, reduce `--sample-size`.
- **File Paths**: Ensure you are running commands from the project root directory.