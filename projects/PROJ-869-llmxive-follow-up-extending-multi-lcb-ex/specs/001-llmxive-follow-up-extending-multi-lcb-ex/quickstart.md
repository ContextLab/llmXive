# Quickstart: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with sufficient RAM).
- Hugging Face account (optional, for model access if required).

## Installation

1. **Clone the Repository**:
```bash
git clone
cd llmxive-follow-up/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```
*Note: This installs `datasets`, `transformers`, `torch` (CPU), `scikit-learn`, `pytest`, `pyarrow`.*

3. **Verify Environment**:
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
# Expected: CUDA available: False (CPU-first)
```

## Data Preparation

1. **Download Datasets**:
The script `code/src/data_loader.py` will automatically download and cache the verified parquet files.
```bash
python code/src/data_loader.py --cache-dir data/raw --verify-checksum
```

2. **Filter Tasks**:
Run the stochasticity filter to select a representative task set.
```bash
python code/src/data_loader.py --filter-stochasticity --output data/processed/filtered_tasks.json
```

## Running the Experiment

### Step 1: Extract Logic Anchors
```bash
python code/src/anchor_extractor.py --input data/processed/filtered_tasks.json --output data/processed/anchors.json
```

### Step 2: Run Blind Condition
```bash
python code/src/inference_engine.py --condition blind --input data/processed/filtered_tasks.json --output results/blind_results.json
```

### Step 3: Run Guided Condition
```bash
python code/src/inference_engine.py --condition guided --input data/processed/filtered_tasks.json --anchors data/processed/anchors.json --output results/guided_results.json
```

### Step 4: Execute & Verify
```bash
python code/src/sandbox_runner.py --input results/blind_results.json results/guided_results.json --timeout 10 --output results/execution_logs.json
```

### Step 5: Analyze & Report
```bash
python code/src/stats_analyzer.py --input results/execution_logs.json --output results/statistical_report.json
```

## Expected Output

- `results/statistical_report.json`: Contains the McNemar's p-value, Pass@1 rates, and error distribution.
- `results/execution_logs.json`: Detailed logs for each task (Pass/Fail, error type).

## Troubleshooting

- **OOM Error**: Ensure you are using the `streaming=True` flag in `data_loader.py`. Reduce batch size to 1.
- **Timeout Errors**: If valid solutions are timing out, the algorithmic complexity may be too high for the 10s limit (log as "Runtime Error" but note in analysis).
- **Anchor Extraction Failed**: If a Python solution is too short, the task is skipped. Check `data/processed/anchors.json` for `status: Failed`.