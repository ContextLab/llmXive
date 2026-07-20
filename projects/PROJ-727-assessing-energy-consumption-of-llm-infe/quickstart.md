# Quickstart Guide: Assessing Energy Consumption of LLM Inference

## Overview
This project quantifies the energy consumption (kWh) and runtime of LLM inference on the HumanEval dataset using CPU-only execution. It measures metrics for three models: GPT-2-small, CodeBERT, and StarCoder-1B.

## Prerequisites
- Python 3.9+
- pip
- A Unix-like environment (Linux/macOS) or WSL on Windows
- Sufficient disk space (~10GB for models and data)

## Installation

1. **Clone the repository** (if not already done) and navigate to the project root.
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: Ensure `requirements.txt` includes `transformers`, `torch`, `codecarbon`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `human-eval`, and `huggingface_hub`.*

4. **Verify the environment**:
 ```bash
 python tests/test_dummy.py::test_dummy_inference
 ```
 *Alternatively, run the entry point script:*
 ```bash
 bash run.sh
 ```
 This will run a lightweight dummy inference test to verify imports and basic functionality without loading full models. It should exit with code 0 and print "Environment Verified".

## Execution

To run the full pipeline (Inference -> Evaluation -> Aggregation -> Analysis -> Visualization):

```bash
bash run.sh
```

**Note**: This process may take several hours on a CPU-only runner. It will:
1. Download the HumanEval dataset.
2. Run inference for GPT-2, CodeBERT, and StarCoder-1B.
3. Evaluate generated completions.
4. Perform statistical analysis (ANOVA, Tukey HSD, Regression).
5. Generate visualizations.

## Expected Artifacts

Upon successful completion, the following files will be generated in the `data/processed/` and `logs/` directories:

### Data Artifacts
- `data/raw/human_eval_data.jsonl`: Raw HumanEval dataset.
- `data/processed/energy_inference_raw.csv`: Raw inference logs (energy, tokens, runtime).
- `data/processed/energy_results_raw.csv`: Joined inference and evaluation results.
- `data/processed/filtered_rows.csv`: Rows filtered out due to null energy or zero tokens.
- `data/processed/energy_results_aggregated.csv`: Clean, aggregated dataset for analysis.
- `data/processed/stats_report.csv`: Statistical analysis results (ANOVA, Tukey, Regression).
- `data/processed/sensitivity_delta.csv`: Sensitivity analysis results.

### Visualization Artifacts
- `data/processed/energy_bar.png`: Bar plot of Energy per Token vs Model.
- `data/processed/tradeoff_scatter.png`: Scatter plot of Energy per Correct Solution vs Accuracy.

### Logs
- `logs/pipeline_duration.log`: Execution time and timing details.

## Verification

To verify the results:
1. Check that `data/processed/energy_results_aggregated.csv` exists and contains non-null values for all required columns.
2. Verify `data/processed/stats_report.csv` contains the ANOVA table and regression coefficients.
3. Ensure `data/processed/energy_bar.png` and `data/processed/tradeoff_scatter.png` exist and have correct labels/legends.
4. Confirm `logs/pipeline_duration.log` shows the total runtime.

## Troubleshooting

- **OOM Errors**: The pipeline is designed for CPU-only execution. If you encounter OOM errors, ensure no other heavy processes are running and that you are using the `StarCoder-1B` model (not the base version) as per project constraints.
- **Missing Data**: If `data/raw/human_eval_data.jsonl` is missing, ensure `code/download.py` runs successfully or manually fetch the dataset.
- **CodeCarbon Errors**: Ensure you have write permissions in the project directory for `codecarbon` to log emissions.

## Project Structure

```
.
├── code/ # Source code modules
├── data/
│ ├── raw/ # Raw datasets
│ └── processed/ # Processed data and results
├── tests/ # Test suite
├── logs/ # Execution logs
├── run.sh # Entry point script
├── requirements.txt # Dependencies
└── quickstart.md # This file
```