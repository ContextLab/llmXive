# Quickstart: Assessing Energy Consumption of LLM Inference for Code Completion

## Prerequisites

-   Python 3.10 or higher.
-   Access to a GitHub Actions runner (or local machine with sufficient RAM).
-   Internet access to download models and datasets.

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `torch` is installed with CPU support only (no CUDA).*

## Running the Benchmark

The entire pipeline is orchestrated by `run.sh`.

```bash
# Execute the full pipeline: download, calibrate, infer, analyze, plot
bash run.sh
```

### What happens during the run?

1.  **Verification**: The script checks for `human-eval` compatibility and runs a dummy test.
2.  **Calibration**: A **CPU-bound load loop** runs to verify `codecarbon` accuracy (simulating inference memory patterns).
3.  **Inference**:
    -   Downloads GPT-2-small, CodeBERT, **StarCoder-1B**.
    -   Runs inference on all HumanEval problems for each model.
    -   Logs energy (kWh) and runtime.
4.  **Analysis**: Performs ANOVA, Tukey HSD, Bootstrap Sensitivity, and Descriptive Regression.
5.  **Visualization**: Generates `energy_per_token_bar.png` and `sustainability_tradeoff.png`.

## Output Artifacts

After completion, the following files will be available in `data/processed/`:

-   `results.csv`: Raw row-level data for all runs.
-   `aggregated_metrics.csv`: Summary statistics per model.
-   `stats_report.txt`: Text output of statistical tests (p-values, coefficients).
-   `energy_per_token_bar.png`: Bar chart of energy per token.
-   `sustainability_tradeoff.png`: Scatter plot of Energy vs. Accuracy.

## Troubleshooting

-   **OOM Error**: If the script fails with "Out of Memory", check logs. The current model selection (StarCoder-1B) should fit; if OOM occurs, it indicates a hardware anomaly.
-   **CodeCarbon Warning**: If `codecarbon` fails to detect power draw, the energy values will be `null`. The script will log a warning and exclude these rows from analysis.
-   **Timeout**: If a model takes too long on a specific problem, the `status` will be `timeout`.

## Reproducibility

To reproduce the results exactly:
1.  Ensure `code/config.py` seeds are unchanged.
2.  Use the same version of `requirements.txt`.
3.  Run on a similar CPU environment (energy values may vary slightly due to hardware differences, but relative trends should hold).