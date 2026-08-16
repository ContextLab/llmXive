# Quickstart Guide: llmXive Follow-up (Extending LoopCoder-v2)

This guide provides instructions for running the pipeline in either **CPU Validation Mode** (for rapid testing with a small sample) or **Full GPU Analysis Mode** (for the complete scientific study).

## Prerequisites

1. **Environment Setup**:
 - Ensure Python 3.10+ is installed.
 - Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
 - Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Configuration**:
 - Verify `code/config.yaml` exists and contains valid paths for `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH`.
 - Set environment variables if paths are not in config:
 ```bash
 export CODELLAMA_CPU_PATH="path/to/codellama/cpu"
 export CODELLAMA_GPU_PATH="path/to/codellama/gpu"
 ```
 - Ensure `HF_TOKEN` is set if downloading models from Hugging Face.

3. **Data Preparation**:
 - Run the data loading and stratification pipeline first:
 ```bash
 python code/src/data_loader.py --mode prepare
 ```
 - This generates `data/processed/filtered_splits.json`, `data/processed/full_splits.json`, and `data/processed/strata_log.json`.

---

## CPU Validation Mode (N=50)

Use this mode to verify the pipeline logic and reproducibility on a small dataset (N=50 samples) within a short timeframe (typically < 1 hour on CPU).

### Steps

1. **Run Entropy Extraction (Sample)**:
 ```bash
 python code/src/entropy.py --input data/processed/filtered_splits.json --output data/processed/entropy_results.csv --sample-size 50
 ```
 *Output*: `data/processed/entropy_results.csv`

2. **Run Convergence Inference (Sample)**:
 ```bash
 python code/src/inference.py --input data/processed/filtered_splits.json --output data/processed/convergence_results_core.csv --k_range [1,2,3] --sample-size 50
 ```
 *Output*: `data/processed/convergence_results_core.csv`

3. **Run Correlation & Survival Analysis**:
 ```bash
 python code/src/survival.py --mode correlation --input-entropy data/processed/entropy_results.csv --input-convergence data/processed/convergence_results_core.csv
 ```
 *Output*: `data/processed/correlation_spearman.json`, `data/processed/correlation_survival.json`

4. **Run Router Simulation**:
 ```bash
 python code/src/analysis.py --mode router --input-entropy data/processed/entropy_results.csv --input-convergence data/processed/convergence_results_core.csv --output data/processed/router_simulation.csv
 ```
 *Output*: `data/processed/router_simulation.csv`, `data/processed/router_metrics.json`

5. **Verify Resource Metrics**:
 ```bash
 python code/src/utils.py --mode validation
 ```
 *Output*: `data/processed/resource_metrics.json`

6. **Generate Validation Report**:
 ```bash
 python code/src/run_validation.py --mode cpu
 ```
 *Output*: `data/processed/validation_report.json`

---

## Full GPU Analysis Mode

Use this mode for the complete scientific study on the full dataset. This requires a GPU with sufficient VRAM and may take several hours.

### Steps

1. **Run Full Entropy Extraction**:
 ```bash
 python code/src/entropy.py --input data/processed/full_splits.json --output data/processed/entropy_results_full.csv
 ```
 *Output*: `data/processed/entropy_results_full.csv`

2. **Run Full Convergence Inference**:
 ```bash
 python code/src/inference.py --input data/processed/full_splits.json --output data/processed/convergence_results_core_full.csv --k_range [1,2,3,4]
 ```
 *Output*: `data/processed/convergence_results_core_full.csv`, `data/processed/convergence_results_sensitivity.csv`

3. **Run Full Correlation & Survival Analysis**:
 ```bash
 python code/src/survival.py --mode full --input-entropy data/processed/entropy_results_full.csv --input-convergence data/processed/convergence_results_core_full.csv
 ```
 *Output*: `data/processed/correlation_results_final.json`

4. **Run Full Router Simulation**:
 ```bash
 python code/src/analysis.py --mode full-router --input-entropy data/processed/entropy_results_full.csv --input-convergence data/processed/convergence_results_core_full.csv --output data/processed/router_results_full.csv
 ```
 *Output*: `data/processed/router_results_full.csv`, `data/processed/flops_savings.json`

5. **Run Robustness & Sensitivity Analysis**:
 ```bash
 python code/src/robustness.py --mode full
 ```
 *Output*: `data/processed/adjusted_pvalues.json`, `data/processed/mixed_effects_results.json`, `data/processed/robustness_summary.json`

6. **Capture Full Analysis Metrics**:
 ```bash
 python code/src/sc005_runner.py --mode gpu --output data/processed/sc005_metrics.json
 ```
 *Output*: `data/processed/sc005_metrics.json`

7. **Generate Final Feasibility Report**:
 ```bash
 python code/src/aggregation.py --mode final
 ```
 *Output*: `data/processed/sc005_final_report.json`

---

## Troubleshooting

- **Model Not Found**: Ensure `CODELLAMA_CPU_PATH` or `CODELLAMA_GPU_PATH` points to a valid local directory containing the model weights, or that `HF_TOKEN` is set for remote access.
- **OSError: Not a valid model identifier**: Verify the model name in the config or environment variable matches a valid Hugging Face repository ID.
- **CUDA Out of Memory**: Reduce the batch size in `code/config.yaml` or switch to a smaller model variant.
- **Missing Data Files**: Ensure `data/processed/` contains the required split files. Re-run `code/src/data_loader.py --mode prepare` if necessary.

## Reproducibility

All experiments use a fixed random seed (default: 42) set via `code/src/utils.py`. To change the seed, update `code/config.yaml` or pass `--seed` to the respective scripts.