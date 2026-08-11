# llmXive GateMem Benchmark - Quick Start Guide

This guide provides step-by-step instructions for setting up the environment, fetching the real dataset, and running the initial evaluation pipeline for the GateMem benchmark extension.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Minimum 14 GB disk space (for streaming the full dataset)
- Minimum 7 GB RAM (for processing)

## 1. Environment Setup

### Clone the Repository
```bash
git clone <repository-url>
cd llmxive-follow-up-extending-gatemem-benc
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install the pinned dependencies from `requirements.txt` to ensure reproducibility:
```bash
pip install -r requirements.txt
```

### Verify Installation
Run the following to ensure all critical packages are available:
```bash
python -c "import datasets; import transformers; import statsmodels; import torch; print('Dependencies verified.')"
```

## 2. Dataset Download

This project uses the **GateMem** dataset hosted on Hugging Face. The data loader is configured to **stream** the dataset to avoid memory issues and will **fail loudly** if the real source is unreachable (no synthetic fallbacks).

### Fetch the Dataset
Run the data loader script to download and validate the dataset:
```bash
python code/utils/data_loader.py --fetch
```

This will:
1. Stream the `gatekeeper/gatemem` dataset (config='default', split='test').
2. Compute and store the SHA256 checksum in `state/artifact_hashes.yaml`.
3. Validate the episode structure against `contracts/dataset.schema.yaml`.

**Note:** If the network is unavailable or the dataset is missing, the script will exit with code 1 and log "Critical: Real Data Fetch Failed".

## 3. Running the Evaluation

The pipeline supports running the Gatekeeper evaluation against baselines on specific domains.

### Run Access Control Evaluation (User Story 1)
Evaluate on the "medical" and "office" domains:
```bash
python code/cli/run_evaluation.py --domains medical,office --mode access_control
```

### Run Full Benchmark Suite
To execute all user stories (Access Control, Utility, Forgetting, Cost Profiling):
```bash
python code/cli/run_evaluation.py --domains medical,office,education,household --mode full
```

### Output Artifacts
Results are saved to the `data/processed/` directory:
- `access_control_results.json`
- `utility_results.json`
- `forgetting_results.json`
- `performance_results.json`
- `combined_metrics.json`

## 4. Testing

Run the unit tests to verify the setup:
```bash
pytest tests/unit/ -v
```

Run contract tests to ensure schema compliance:
```bash
pytest tests/contract/ -v
```

Specifically verify the documentation exists:
```bash
pytest tests/unit/test_docs.py::test_quickstart_exists
```

## Troubleshooting

- **Dataset Fetch Failed**: Ensure your internet connection is active and you have access to Hugging Face. Check `logs/data_loader.log` for specific errors.
- **Memory Errors**: The pipeline uses streaming. If you encounter OOM errors, ensure you are not loading the entire dataset into memory at once in custom scripts.
- **CUDA Errors**: The code enforces CPU execution (`device='cpu'`). If you see CUDA errors, verify your environment variables or ensure `torch` is not attempting to use a GPU.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` to ensure all packages are installed.

## Next Steps

- Review `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md` for detailed feature requirements.
- Implement User Story 2 (Utility/Forgetting) if not yet completed.
- Review the generated `data/results/final_benchmark_report.md` after a full run.
