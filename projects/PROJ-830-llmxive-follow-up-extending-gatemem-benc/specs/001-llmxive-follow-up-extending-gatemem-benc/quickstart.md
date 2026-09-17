# Quickstart: GateMem Benchmark Extension

This guide provides step-by-step instructions to set up the environment, fetch the real GateMem dataset, and run the initial evaluation pipeline for the llmXive follow-up project.

## Prerequisites

- Python 3.9+
- pip
- At least 14GB disk space and 8GB RAM (for streaming the full dataset)

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
# Navigate to project root
cd PROJ-830-llmxive-follow-up-extending-gatemem-benc

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Dataset Download Guide

The project uses the **GateMem** dataset hosted on Hugging Face. This task requires the real data; no synthetic fallbacks are permitted.

### Automatic Fetch (Recommended)

Run the data loader script to fetch, validate, and checksum the dataset:

```bash
python code/utils/data_loader.py
```

This script will:
1. Stream the `gatekeeper/gatemem` dataset (split='test') to `data/raw/gatemem_test.jsonl`.
2. Verify required fields (`outcome`, `predictors`, `covariates`, `leak-target`, `roles`, `domains`).
3. Compute SHA-256 checksums and store them in `state/artifact_hashes.yaml`.
4. **Fail loudly** if the fetch fails or checksums do not match.

### Manual Fetch (Alternative)

If you need to manually verify the source:

```python
from datasets import load_dataset

# Stream to avoid memory issues
ds = load_dataset("gatekeeper/gatemem", split="test", streaming=True)
# Save to local file if needed
# ds.to_json("data/raw/gatemem_test.jsonl")
```

**Note**: Ensure your internet connection is active. The loader will raise a `ConnectionError` if the real source is unreachable.

## 3. Basic Run Commands

### Run Gatekeeper Evaluation

Execute the Gatekeeper pipeline on specific domains (e.g., medical, office):

```bash
python code/cli/run_evaluation.py --domains medical,office --mode gatekeeper
```

### Run Baseline Evaluation

Execute the baseline pipelines (Retrieval-only and Long-Context):

```bash
python code/cli/run_evaluation.py --domains medical,office --mode baseline
```

### Run Full Statistical Analysis

Once results are generated, run the statistical comparison (LMM, Stratified, or GLM):

```bash
python code/utils/stats.py --run-full-pipeline
```

## 4. Output Verification

After running the evaluation, verify the following artifacts exist:

- `data/processed/gatekeeper_results.json`
- `data/processed/baseline_results.json`
- `data/processed/unified_metrics.json`
- `data/results/final_benchmark_report.md`

Check the logs in `logs/` for any `ConnectionError` or `ValueError` indicating data integrity issues.

Run the full test suite to ensure all components are working correctly:

- **Data Fetch Failed**: Ensure you have a stable internet connection and the Hugging Face Hub is accessible. Check `logs/data_loader.log` for specific error messages.
- **Checksum Mismatch**: The data file in `data/raw/` may be corrupted. Delete `data/raw/gatemem_test.jsonl` and `state/artifact_hashes.yaml`, then re-run the data loader.
- **Memory Errors**: The script uses `streaming=True` by default. Ensure you are not manually loading the full dataset into memory in custom scripts.