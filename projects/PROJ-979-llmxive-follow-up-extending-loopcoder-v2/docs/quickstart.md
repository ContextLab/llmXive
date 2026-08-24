# Quickstart Guide: llmXive Follow-up (LoopCoder-v2 Extension)

This guide provides instructions for running the llmXive analysis pipeline.
The project supports two execution modes: **CPU Validation Mode** (fast, small sample)
and **Full GPU Analysis** (complete dataset, requires GPU).

## Prerequisites

1. **Environment**: Python 3.10+
2. **Dependencies**: Install required packages:
 ```bash
 cd code
 pip install -r requirements.txt
 ```
3. **Hugging Face Token**: Set `HF_TOKEN` environment variable for model access.
4. **Kaggle Credentials** (for GPU mode): Set `KAGGLE_USER` and `KAGGLE_KEY` if offloading to Kaggle.

---

## Mode 1: CPU Validation Mode (N=50)

Use this mode for quick validation of the pipeline logic on a small subset of data.
This mode runs entirely on CPU and is designed to complete in minutes.

### Steps

1. **Prepare Data**:
 Ensure the raw datasets are fetched. If not done, run:
 ```bash
 python code/src/data_loader.py --mode fetch
 ```

2. **Run Validation Pipeline**:
 Execute the validation script which processes a small sample (N=50).
 ```bash
 python code/src/run_validation.py --sample-size 50 --mode cpu
 ```
 *This will generate `data/processed/entropy_results.csv`, `data/processed/convergence_results_core.csv`, and `validation_report.json`.*

3. **Verify Outputs**:
 Check that the following files exist in `data/processed/`:
 - `entropy_results.csv`
 - `convergence_results_core.csv`
 - `validation_report.json`

---

## Mode 2: Full GPU Analysis

Use this mode for the complete statistical analysis on the full dataset.
This requires a GPU environment (e.g., Kaggle, local GPU server).

### Steps

1. **Prepare Data**:
 Ensure raw datasets are fetched and processed:
 ```bash
 python code/src/data_loader.py --mode process
 ```

2. **Run GPU Offload Script** (Recommended for Kaggle):
 If using Kaggle, submit the job:
 ```bash
 bash code/run_gpu.sh
 ```
 *This script pushes the code to Kaggle, waits for completion, and downloads artifacts.*

3. **Or Run Locally on GPU**:
 If running locally with a GPU:
 ```bash
 python code/src/sc005_runner.py --mode full
 ```
 *This will execute the full entropy extraction, convergence inference, and correlation analysis.*

4. **Verify Outputs**:
 The following artifacts should be present in `data/processed/`:
 - `entropy_results.csv`
 - `convergence_results_core.csv`
 - `correlation_results_final.json`
 - `router_results.csv`
 - `sc005_final_report.json`

---

## Troubleshooting

- **Model Not Found**: Ensure `HF_TOKEN` is set and the model `codellama/CodeLlama-1.3b-Instruct-hf` is accessible.
- **CUDA Out of Memory**: Reduce batch size or use a smaller model variant if running locally.
- **Missing Data Files**: Re-run `code/src/data_loader.py` to fetch and process datasets.