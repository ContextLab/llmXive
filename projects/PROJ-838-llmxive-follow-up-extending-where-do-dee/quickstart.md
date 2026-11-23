# Quick Start Guide: llmXive Deep-Research Analysis

This guide walks you through running the full analysis pipeline to reproduce the
"Where Do Deep-Research Agents Go Wrong?" study.

## Prerequisites

- Python 3.11 or higher
- Internet connection (to download the TELBench dataset)
- ~15 GB disk space (for dataset and processed artifacts)

## Step 1: Environment Setup

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

## Step 2: Run the Pipeline

Execute the main orchestration script:

```bash
python code/pipeline.py --config code/config.py
```

**What this does:**
1. **Download**: Fetches `NJU-LINK/TELBench` from HuggingFace (streaming mode)
2. **Parse**: Extracts early spans (first 30%) and builds co-reference graphs
3. **Metrics**: Calculates Global Connectivity and Average Branching Factor
4. **Split**: Stratifies data into Train/Test sets
5. **Evaluate**: Computes the 20th percentile threshold and predicts collapse
6. **Report**: Generates `results_report.json` and all intermediate artifacts

**Expected Runtime:** ~10-30 minutes (depending on dataset size and CPU speed)

## Step 3: Inspect Results

After completion, check `data/processed/` for:

- `results_report.json`: The final comprehensive report
- `evaluation_results.json`: Structured metrics (precision, recall, F1)
- `threshold_config.json`: The primary threshold value
- `sensitivity_heatmap.png`: Visualization of threshold robustness
- `linear_reasoning_report.json`: Analysis of chain-like reasoning patterns

## Troubleshooting

### "No such file or directory: code/pipeline.py"
Ensure you are running from the project root directory.

### "Dataset not found"
The pipeline requires internet access to fetch `NJU-LINK/TELBench`. Check your connection.

### "Insufficient samples for threshold calculation"
If the success class has fewer than 5 samples, the pipeline will halt. This is a
statistical safety check (see `code/evaluator.py::calculate_20th_percentile_threshold`).

## Validation

To verify the pipeline ran correctly:

1. Check that `data/processed/results_report.json` exists and is non-empty.
2. Run the test suite:
 ```bash
 pytest tests/ -v
 ```
3. Verify formatting:
 ```bash
 black --check code/ && ruff check code/
 ```

## Next Steps

- Read `research.md` for the full scientific context and methodology.
- Review `specs/001-gene-regulation/` for detailed user stories and requirements.
