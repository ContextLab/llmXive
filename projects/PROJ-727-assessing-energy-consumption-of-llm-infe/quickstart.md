# Quickstart Guide

## Project: Assessing Energy Consumption of LLM Inference for Code Completion

This guide provides instructions to run the full pipeline and verify the generated artifacts.

## Prerequisites

- Python 3.9+
- `requirements.txt` installed
- A CPU-based environment (GPU not required, but supported if configured)

## Setup

1. **Clone the repository**
2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
3. **Verify environment** (Optional but recommended):
 ```bash
 python code/calibration.py
 ```

## Running the Pipeline

Execute the full pipeline using the entry point script:

```bash
./run.sh
```

Or manually via Python:

```bash
python code/main.py
```

**Note**: The pipeline performs the following steps:
1. Downloads HumanEval dataset (if not present).
2. Runs inference for GPT-2-small, CodeBERT, and StarCoder-1B.
3. Evaluates code completions.
4. Aggregates results.
5. Performs statistical analysis (ANOVA, Tukey, Regression).
6. Generates visualizations.

## Expected Artifacts

Upon successful completion, the following files should exist:

### Data
- `data/raw/human_eval_data.jsonl`
- `data/processed/energy_inference_raw.csv`
- `data/processed/energy_results_raw.csv`
- `data/processed/filtered_rows.csv`
- `data/processed/energy_results_aggregated.csv`
- `data/processed/stats_report.csv`
- `data/processed/sensitivity_delta.csv`

### Visualizations
- `data/processed/energy_bar.png`
- `data/processed/tradeoff_scatter.png`

### Logs
- `logs/pipeline_duration.log`
- `logs/final_validation.log`

## Validation

To verify all artifacts were generated correctly:

```bash
python code/final_validation.py
```

This script checks for the existence and content integrity of all required files.

## Troubleshooting

- **OOM Errors**: Ensure you are running on a machine with sufficient RAM. The pipeline is optimized for CPU but large models may still require significant memory.
- **CodeCarbon Errors**: Ensure `codecarbon` is installed and your environment has access to power monitoring APIs (often requires root or specific permissions on some systems).
- **Timeouts**: If the pipeline times out, reduce the number of problems processed in `code/config.py` (not recommended for final runs).

## License

See LICENSE file in the repository root.
