# Quickstart Guide: Assessing Energy Consumption of LLM Inference

## Prerequisites

- Python 3.9+
- pip
- 14GB+ disk space
- 8GB+ RAM (CPU-only execution)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The full pipeline can be executed using the `run.sh` script:

```bash
chmod +x run.sh
./run.sh
```

### Pipeline Steps

1. **Environment Verification**: Runs a lightweight dummy inference test to ensure the environment is ready.
2. **Data Download**: Fetches the HumanEval dataset and saves it to `data/raw/human_eval_data.jsonl`.
3. **Checksum Verification**: Computes and stores SHA-256 hash of the downloaded data in `state/projects/PROJ-727-assessing-energy-consumption-of-llm-infe.yaml`.
4. **Calibration**: Validates `codecarbon` power draw detection with a CPU-bound load loop.
5. **Inference**: Runs GPT-2-small, CodeBERT, and StarCoder-1B on HumanEval problems, logging energy usage.
6. **Evaluation**: Evaluates generated completions and joins results with energy metrics.
7. **Aggregation**: Filters invalid rows and creates the clean aggregated dataset.
8. **Statistical Analysis**: Performs ANOVA, Tukey HSD, and regression analysis.
9. **Visualization**: Generates bar and scatter plots.

## Expected Artifacts

After successful execution, the following files should exist:

### Data
- `data/raw/human_eval_data.jsonl` (HumanEval dataset)
- `data/processed/energy_inference_raw.csv`
- `data/processed/energy_results_raw.csv`
- `data/processed/energy_results_aggregated.csv`
- `data/processed/filtered_rows.csv`
- `data/processed/stats_report.csv`
- `data/processed/sensitivity_delta.csv`
- `data/processed/scatter_slope.txt`

### Visualizations
- `data/processed/energy_bar.png` (Energy per Token vs Model)
- `data/processed/tradeoff_scatter.png` (Energy per Correct vs Accuracy)

### State & Logs
- `state/projects/PROJ-727-assessing-energy-consumption-of-llm-infe.yaml` (includes artifact_hashes)
- `logs/pipeline_duration.log`
- `codecarbon_logs/` (directory with energy logs per model)

## Verification

To verify checksums manually:
```bash
python -m code.checksum_verify verify
```

To re-compute and store checksums:
```bash
python -m code.checksum_verify store
```

## Troubleshooting

- **OOM Errors**: Ensure you are using StarCoder-1B (not StarCoder-base) as per project constraints.
- **Missing Data**: Run `python -m code.download` to re-download the HumanEval dataset.
- **Checksum Mismatch**: Re-run the download task and verify the checksum again.