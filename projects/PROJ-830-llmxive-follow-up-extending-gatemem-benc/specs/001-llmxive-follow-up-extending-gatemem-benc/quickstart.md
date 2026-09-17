# Quickstart Guide: GateMem Benchmark Extension

This guide provides step-by-step instructions to set up the environment, fetch the real GateMem dataset, and run the initial evaluation pipeline for the llmXive follow-up project.

## Prerequisites

- Python 3.11+
- pip
- Access to Hugging Face Hub (for dataset/model download)

## 1. Environment Setup

### Install Dependencies

Ensure you are in the project root directory and install the required packages:

```bash
pip install -r requirements.txt
```

**Required Packages**: `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`, `ruff`.

### Verify Installation

Run the setup verification test:

```bash
pytest tests/unit/test_setup.py::test_directory_structure
```

This ensures all necessary directories (`code/`, `data/`, `tests/`, `state/`, `logs/`, etc.) are present.

## 2. Dataset Configuration & Download

The pipeline relies on the real GateMem dataset. **Do not use synthetic data.**

### Configure Dataset ID

The dataset ID is read from the environment variable `DATASET_ID` or `code/utils/config.py`.

**Option A: Environment Variable (Recommended)**
```bash
export DATASET_ID="your_huggingface_dataset_id"
```

**Option B: Configuration File**
Edit `code/utils/config.py` (create if missing) and set:
```python
DATASET_ID = "your_huggingface_dataset_id"
```

> **Note**: If `DATASET_ID` is not configured, the data loader will raise a `FileNotFoundError` immediately.

### Fetch the Dataset

Run the data loader script to fetch and validate the dataset:

```bash
python code/utils/data_loader.py
```

**What this script does:**
1. Fetches the dataset from Hugging Face using `datasets.load_dataset()`.
2. Computes and stores a SHA256 checksum in `state/artifact_hashes.yaml` (key: `gatemem_test`).
3. Validates the presence of required fields (`outcome`, `predictors`, `covariates`, `leak-target`).
4. **Fails loudly** if the fetch fails or validation errors occur. No synthetic fallbacks are used.

**Output:**
- Raw data is saved to `data/raw/`.
- Processed data is saved to `data/processed/`.

## 3. Running the Evaluation

The evaluation pipeline compares the Gatekeeper model against Retrieval-only and Long-Context baselines.

### Run Access Control Evaluation (User Story 1)

Evaluate the "medical" and "office" domains:

```bash
python code/cli/run_evaluation.py --domains medical,office
```

**Output:**
- `data/processed/gatekeeper_results.json`
- `data/processed/baseline_retrieval_results.json`
- `data/processed/baseline_longcontext_results.json`

### Run Utility & Forgetting Evaluation (User Story 2)

Evaluate the "education" and "household" domains:

```bash
python code/cli/run_evaluation.py --domains education,household --metrics utility,forgetting
```

### Run Profiling (User Story 3)

Generate performance metrics (latency, RAM):

```bash
python code/cli/run_evaluation.py --profile
```

## 4. Verification

Run the full test suite to ensure all components are working correctly:

```bash
pytest tests/
```

**Key Tests:**
- `tests/unit/test_docs.py::test_quickstart_exists`: Verifies this guide exists.
- `tests/unit/test_data_loader.py::test_fetch_streaming`: Verifies real data fetching.
- `tests/contract/test_dataset_schema.py`: Validates data structure.
- `tests/contract/test_results_schema.py`: Validates output structure.

## Troubleshooting

- **Dataset ID Error**: If you see "Dataset ID not configured", ensure `DATASET_ID` is set in your environment or `code/utils/config.py`.
- **Checksum Mismatch**: If you see "Checksum mismatch", delete `state/artifact_hashes.yaml` and re-run `python code/utils/data_loader.py`.
- **Memory Errors**: The pipeline uses streaming for large datasets. If you encounter OOM errors, ensure your runner has at least 16GB RAM or reduce the batch size in `code/utils/data_loader.py`.

## Next Steps

- Review `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md` for detailed user stories.
- Check `code/gatekeeper/pipeline.py` for implementation details.
- Generate the final report with `python code/cli/generate_report.py`.