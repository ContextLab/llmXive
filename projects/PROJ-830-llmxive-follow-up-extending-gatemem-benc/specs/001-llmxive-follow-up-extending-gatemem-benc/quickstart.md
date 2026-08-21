# llmXive Follow-up: Extending GateMem Benchmark

This guide provides step-by-step instructions to set up the environment, fetch the real dataset, and run the initial evaluation for the GateMem benchmark extension.

## Prerequisites

- Python 3.9+
- pip
- Git

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Ensure the following packages are installed (as per `requirements.txt`):
- `datasets`
- `transformers`
- `scikit-learn`
- `statsmodels`
- `pandas`
- `pyyaml`
- `pytest`
- `huggingface_hub`

## 2. Dataset Download

This project uses the **GateMem** dataset from HuggingFace. The data loader (`code/utils/data_loader.py`) is configured to stream the dataset to handle memory constraints.

The dataset ID is `gatekeeper/gatemem` with configuration `default` and split `test`. [UNRESOLVED-CLAIM: c_634067af — status=not_enough_info]

### Manual Fetch (Optional)

If you wish to verify the dataset availability before running the full pipeline:

```python
from code.utils.data_loader import fetch_dataset

# This will stream the data and compute a checksum
# It will raise ConnectionError if the fetch fails (no synthetic fallback)
try:
 data = fetch_dataset()
 print(f"Successfully loaded {len(data)} episodes")
except ConnectionError as e:
 print(f"Critical: Real Data Fetch Failed - {e}")
 sys.exit(1)
```

The dataset will be cached by the `datasets` library, and a checksum will be stored in `state/artifact_hashes.yaml`.

## 3. Running the First Evaluation

The pipeline is designed to run on CPU-only environments for reproducibility.

### Run Access Control Evaluation (User Story 1)

This executes the Gatekeeper and Baseline pipelines on the "medical" and "office" domains to measure unauthorized information leakage.

```bash
python code/cli/run_evaluation.py --domains medical,office --stage us1
```

**Expected Output:**
- Results written to `data/processed/gatekeeper_results.json`
- Results written to `data/processed/baseline_retrieval_results.json`
- Results written to `data/processed/baseline_longcontext_results.json`
- Access Control metrics calculated and saved to `data/processed/access_control_results.json`

### Run Utility & Forgetting Evaluation (User Story 2)

To evaluate task success and forgetting compliance:

```bash
python code/cli/run_evaluation.py --domains education,household --stage us2
```

**Expected Output:**
- Unified metrics in `data/processed/unified_metrics.json`
- Statistical comparison results in `data/processed/statistical_results.json`

### Run Profiling (User Story 3)

To measure latency and RAM usage:

```bash
python code/cli/run_evaluation.py --domains medical --stage us3
```

**Expected Output:**
- Performance comparison in `data/processed/performance_results.json`

## 4. Verification

Run the contract tests to ensure outputs match the required schemas:

```bash
pytest tests/contract/ -v
```

Run the unit tests for documentation and core logic:

```bash
pytest tests/unit/test_docs.py::test_quickstart_exists -v
pytest tests/unit/test_data_loader.py::test_fetch_streaming -v
pytest tests/unit/test_metrics.py::test_access_control_calculation -v
```

## 5. Troubleshooting

### Data Fetch Failed
If you see `Critical: Real Data Fetch Failed`, ensure you have an active internet connection and the HuggingFace dataset `gatekeeper/gatemem` is accessible. The system does **not** support synthetic fallbacks.

### Memory Errors
The pipeline uses streaming (`streaming=True`) by default. If you encounter memory issues, ensure no other heavy processes are running. The `state/artifact_hashes.yaml` file indicates the checksum of the downloaded data.

### Model Loading Errors
The classifier uses `facebook/distilbert-base-uncased` in CPU mode. [UNRESOLVED-CLAIM: c_f754392b — status=not_enough_info] If the model fails to load, check your cache directory or retry the fetch. The system implements a single retry mechanism before exiting.

## 6. Project Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and processed data artifacts
- `tests/`: Unit, contract, and integration tests
- `specs/`: Design documents and this quickstart guide
- `state/`: Runtime state (checksums, logs)
- `templates/`: Prompt templates used in evaluation

For more details, refer to the `tasks.md` file for the full task list and dependencies.
