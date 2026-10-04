# Quick Start Guide: llmXive Pipeline

This guide provides step-by-step instructions to set up the full environment, download real data, and run the complete pipeline.

**⚠️ Critical Requirement**: This pipeline requires a full-environment re-execution baseline to establish ground truth. Do not attempt to use "static-only" shortcuts, as they violate the project's safety constraints and will result in invalid models.

## Step 1: Environment Setup

1. **Install Python 3.11**: Ensure you have Python 3.11 or higher installed.
2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: This installs `datasets`, `tree-sitter`, `scikit-learn`, `pandas`, `networkx`, `radon`, and `pytest`.*

## Step 2: Data Download

The pipeline fetches real datasets from HuggingFace. No manual download is required, but you must have network access.

Run the ingestion script:
```bash
python code/scripts/ingest.py
```

**Expected Behavior**:
- The script connects to HuggingFace Hub.
- It downloads `swe_bench_subset` and `agentbench_subset`.
- It parses the data and writes `data/processed/ground_truth.csv`.
- **Failure Condition**: If the network is unreachable or the dataset IDs are invalid, the script will raise an exception. **It will NOT generate synthetic data.**

## Step 3: Feature Extraction

Once ground truth is established, extract structural features:

```bash
python code/scripts/extract_features.py
python code/scripts/generate_features.py
```

**Output**:
- `data/processed/features.csv`: The final dataset with structural metrics.
- `data/graphs/`: JSON files containing dependency graphs for traceability.

## Step 4: Model Training

Train the predictive models and identify safe thresholds:

```bash
python code/scripts/train_model.py
```

**Output**:
- `models/`: Trained `.pkl` files.
- `data/processed/model_report.json`: Contains the FNR analysis and decision boundary.
- `data/processed/threshold_sweep.json`: Sensitivity analysis results.

## Step 5: Verification

Verify that all artifacts are present and checksummed:

```bash
python code/scripts/checksum_artifacts.py
```

## Troubleshooting

- **GPU Detected**: The pipeline explicitly checks for GPU usage. If `nvidia-smi` or `torch.cuda` is available, the `baseline_runner` will raise an exception. Run on a CPU-only machine or disable GPU visibility.
- **Dataset Fetch Failed**: Ensure your HuggingFace token is configured (`huggingface-cli login`) if accessing gated datasets, or check your internet connection.
- **Timeout Errors**: If tasks are timing out, check the `baseline_runner.py` configuration. Tasks marked "Timeout/Fail" are valid ground truth.

## Next Steps

- Read `usage_guide.md` for detailed examples of interpreting results.
- Consult `api_reference.md` for the full API documentation of the scripts.
