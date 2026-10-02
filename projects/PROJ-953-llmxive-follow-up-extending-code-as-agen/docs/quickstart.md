# Quickstart Guide: llmXive Pipeline

This guide provides step-by-step instructions to set up the environment, download real data, and run the full pipeline.

**⚠️ CRITICAL REQUIREMENT**: This project relies on **REAL** data from SWE-bench and AgentBench. The pipeline **MUST** be executed in a full environment capable of running the baseline tests. **Do not attempt to run this pipeline with synthetic or mocked data.** If the real data fetch fails, the script will raise an exception; do not bypass this check.

## Prerequisites

- Python 3.11+
- pip
- ~14 GB disk space (for datasets and intermediate files)
- CPU-only environment (No GPU/CUDA required or allowed)

## Step 1: Environment Setup

1. **Clone and setup**:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-code-as-agen
 ```

2. **Create and activate virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify GPU is NOT available** (Optional but recommended):
 ```bash
 python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
 # Should print: CUDA available: False
 ```
 If CUDA is available, the `baseline_runner.py` script will fail to enforce the CPU-only constraint.

## Step 2: Data Download

The pipeline automatically downloads data when `ingest.py` is run. However, ensure you have a stable internet connection.

**Note**: The datasets are large. Ensure you have sufficient disk space.

## Step 3: Run the Pipeline

Execute the scripts in the following order. Each step produces artifacts required by the next.

### 3.1 Ingest Datasets
```bash
python code/scripts/ingest.py
```
- Downloads SWE-bench and AgentBench subsets.
- Generates `data/processed/ground_truth.csv`.
- **Error Handling**: If download fails, the script exits with a non-zero code. No synthetic data is generated.

### 3.2 Run Baseline Execution
```bash
python code/scripts/baseline_runner.py
```
- Sets up virtual environments for each task.
- Executes tests to determine Pass/Fail/Timeout.
- Updates `ground_truth.csv` with `dynamic_execution_outcome`.
- **Timeouts**: Tasks exceeding the time limit are marked "Timeout/Fail".
- **GPU Check**: Fails immediately if GPU resources are detected.

### 3.3 Extract Structural Features
```bash
python code/scripts/extract_features.py
```
- Parses code using `tree-sitter`.
- Calculates metrics (complexity, depth, LOC).
- Generates `data/processed/features.csv` and graph files in `data/graphs/`.

### 3.4 Train Predictive Model
```bash
python code/scripts/train_model.py
```
- Trains Logistic Regression and Random Forest models.
- Performs sensitivity analysis to find optimal thresholds.
- Generates `models/` artifacts and `data/processed/model_report.json`.

## Step 4: Verify Results

Check the generated artifacts:
- `data/processed/ground_truth.csv`: Ensure no nulls in `task_id`, `code_diff`, `dynamic_execution_outcome`.
- `data/processed/features.csv`: Verify all metrics are populated.
- `data/processed/model_report.json`: Check for the `unsafe` flag and `framing` field.

## Troubleshooting

- **Download Failed**: Ensure internet connectivity and HuggingFace access. The script will not proceed with fake data.
- **Timeout Errors**: Increase the timeout limit in the configuration if tasks are consistently timing out, but be aware of the 6-hour total runtime constraint.
- **GPU Detected**: If the baseline runner fails with a GPU error, ensure your environment is CPU-only.

## Next Steps

For detailed examples and API documentation, see the [Usage Guide](usage_guide.md) and [API Reference](api_reference.md).
