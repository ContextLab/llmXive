# Quickstart Guide: Assessing Energy Consumption of LLM Inference

This guide provides instructions to run the full pipeline for assessing the energy consumption of LLM inference on code completion tasks (HumanEval).

## Prerequisites

- Python 3.10+
- pip
- Sufficient RAM (minimum 8GB recommended for StarCoder-1B on CPU)
- Internet connection (to download HumanEval dataset and models)

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: If `requirements.txt` is missing, ensure it is created with the following packages:*
 - transformers
 - torch-cpu
 - codecarbon
 - pandas
 - numpy
 - scipy
 - statsmodels
 - matplotlib
 - seaborn
 - human-eval
 - huggingface_hub

## Running the Pipeline

The entire pipeline can be executed via the `run.sh` entry point. This script:
1. Verifies the environment (imports `human_eval` and runs a trivial dummy test).
2. Downloads the HumanEval dataset.
3. Runs inference for GPT-2-small, CodeBERT, and StarCoder-1B.
4. Evaluates the generated solutions.
5. Performs statistical analysis (ANOVA, Tukey HSD, Regression).
6. Generates sustainability visualizations.

### Execution Command

```bash
chmod +x run.sh
./run.sh
```

**Note**: Running on a CPU-only environment may take several hours. Ensure your system is stable and not under heavy load.

## Expected Artifacts

Upon successful completion, the following files will be generated in the `data/` and `data/processed/` directories:

### Raw Data
- `data/raw/human_eval_data.jsonl`: The downloaded HumanEval dataset.

### Processed Results
- `data/processed/energy_results_raw.csv`: Raw inference logs including energy (kWh), runtime, and tokens generated.
- `data/processed/energy_results_aggregated.csv`: Cleaned and aggregated results (filtered for nulls/zero tokens).
- `data/processed/stats_report.csv`: Statistical summary including ANOVA, Tukey HSD, and regression results.
- `data/processed/sensitivity_delta.csv`: Sensitivity analysis results (perturbation impact).
- `data/processed/scatter_slope.txt`: Calculated slope for the trade-off scatter plot.

### Visualizations
- `data/processed/energy_bar.png`: Bar plot of Energy per Token vs. Model ID.
- `data/processed/tradeoff_scatter.png`: Scatter plot of Energy per Correct Solution vs. Pass@1 Accuracy.

## Troubleshooting

- **OOM Errors**: If you encounter Out-Of-Memory errors, ensure no other heavy processes are running. The pipeline attempts to unload models sequentially, but CPU memory is limited.
- **CodeCarbon Errors**: If `codecarbon` fails to detect power draw, run `python code/calibration.py` to validate the environment.
- **Model Download Failures**: Ensure you have a stable internet connection and sufficient disk space (models are several GBs).
- **Dummy Test Failure**: If `run.sh` exits with code 1 during the dummy test, verify your Python environment and `human-eval` installation.

## Configuration

Configuration constants (model IDs, seeds, max tokens) are defined in `code/config.py`.
- **Models**: GPT2-small, CodeBERT, StarCoder-1B (substituted for StarCoder-base due to RAM constraints).
- **Temperature**: 0.0 (deterministic generation).
- **Seeds**: Fixed seeds for reproducibility.

## License

This project is part of the llmXive automated science pipeline.