# llmXive Follow-up: Extending GateMem Benchmark
## Quickstart Guide

This guide provides step-by-step instructions for setting up the environment, fetching the real dataset, and running the initial evaluation for the GateMem benchmark extension.

---

## 1. Environment Setup

### Prerequisites
- Python 3.9+
- pip package manager
- Git (for cloning the repository)

### Installation Steps

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-root>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: `requirements.txt` includes `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, and `huggingface_hub`.*

---

## 2. Dataset Download & Verification

This project uses the **GateMem** dataset from HuggingFace. The data loader is configured to **stream** the dataset to handle memory constraints and **strictly forbids** synthetic fallbacks.

### Automatic Fetching
The data loading pipeline (`code/utils/data_loader.py`) automatically fetches the dataset when run.

- **Source**: HuggingFace ID `gatekeeper/gatemem`
- **Configuration**: `default`
- **Split**: `test`
- **Mode**: Streaming (`streaming=True`)

### Manual Verification (Optional)
To verify the dataset exists and is accessible before running the full pipeline:

```python
from code.utils.data_loader import fetch_dataset

try:
 dataset = fetch_dataset()
 print(f"Dataset loaded successfully. Number of episodes: {len(dataset)}")
except ConnectionError as e:
 print(f"Critical: Real Data Fetch Failed - {e}")
 exit(1)
```

**Important**: If the network is unavailable or the dataset ID is incorrect, the script will raise a `ConnectionError` and exit with code 1. No synthetic data will be generated.

---

## 3. Running the First Evaluation

The evaluation pipeline compares the **Gatekeeper** method against **Baseline** configurations (Retrieval-only and Long-Context).

### Run Access Control Evaluation (User Story 1)

Execute the pipeline for the "medical" and "office" domains to verify Access Control scores:

```bash
python code/cli/run_evaluation.py --domains medical,office --phase us1
```

**Expected Output**:
- `data/processed/gatekeeper_results.json`
- `data/processed/baseline_retrieval_results.json`
- `data/processed/baseline_longcontext_results.json`
- `data/processed/access_control_results.json`

### Run Full Benchmark (All User Stories)

To run the complete suite (Access Control, Utility, Forgetting, and Profiling):

```bash
python code/cli/run_evaluation.py --domains medical,office,education,household --phase all
```

---

## 4. Verification & Testing

Run the contract and unit tests to ensure the setup is correct:

```bash
# Run all tests
pytest tests/ -v

# Specifically test the quickstart documentation
pytest tests/unit/test_docs.py::test_quickstart_exists -v
```

---

## 5. Troubleshooting

### "ConnectionError: Real Data Fetch Failed"
- Ensure you have an active internet connection.
- Verify the HuggingFace dataset ID `gatekeeper/gatemem` is correct and accessible.
- Check if you need to log in to HuggingFace (`huggingface-cli login`) if the dataset is gated.

### "ModuleNotFoundError: No module named 'code'"
- Ensure you are running the script from the project root directory.
- Add the project root to `PYTHONPATH`: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

### Memory Issues
- The dataset is configured to stream. If you encounter OOM errors, ensure no other heavy processes are running.
- Check `data/processed/` for intermediate files; ensure sufficient disk space.

---

## 6. Next Steps

After successfully running the initial evaluation:
1. Review `data/results/final_benchmark_report.md` (generated after Phase 3-5).
2. Analyze failure cases in `data/samples/failure_cases.json`.
3. Consult `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md` for detailed user stories and implementation plans.