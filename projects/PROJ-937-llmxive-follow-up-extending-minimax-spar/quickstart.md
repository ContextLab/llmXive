# Quickstart Guide: CPU-Only Execution

This guide provides instructions for running the llmXive sparse attention evaluation pipeline on a CPU-only environment without GPU acceleration or quantization.

## Prerequisites

- Python 3.11 or higher
- 7 GB+ available RAM (14 GB+ recommended for full dataset processing)
- Multi-core CPU (4+ cores recommended)
- Internet connection (for initial dataset download)

## Installation

1. Clone the repository and navigate to the project root:
```bash
git clone <repository-url>
cd llmxive-follow-up-extending-minimax-spar
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The system enforces CPU-only execution by default. Key configuration options are managed in `code/utils/config.py`:

- `device`: Always set to "cpu"
- `seed`: Random seed for reproducibility (default: 42)
- `memory_threshold`: RAM usage threshold for early exit (default: 6.5 GB)
- `timeout_seconds`: Maximum execution time (default: 21600 seconds / 6 hours)

## Running the Pipeline

### Step 1: Download and Verify RULER Dataset

The pipeline requires the RULER dataset from HuggingFace. This step downloads and verifies the data integrity:

```bash
python code/data/loader.py
```

This will:
- Download the dataset to `data/raw/`
- Verify file integrity using SHA256 checksums
- Fail loudly if the download fails or checksums don't match

### Step 2: Run the Baseline (Dense Attention)

Execute the dense attention baseline to establish ground truth metrics:

```bash
python code/eval/baseline_runner.py
```

This generates baseline metrics and selection sets for comparison.

### Step 3: Run Heuristic Experiments

Execute the three heuristics (Block Entropy, Gradient Magnitude, Recency Bias):

```bash
python code/main.py --heuristic block_entropy
python code/main.py --heuristic gradient_magnitude
python code/main.py --heuristic recency_bias
```

Or run all heuristics in sequence:

```bash
python code/main.py --run-all
```

### Step 4: Generate Benchmark Report

Aggregate results and generate the final statistical report:

```bash
python code/eval/report_generator.py
```

This produces `results/benchmark_report.json` containing:
- F1 scores for each heuristic
- Paired t-test and Wilcoxon signed-rank test results
- Holm-Bonferroni corrected p-values
- Sensitivity analysis tables
- False positive rates

### Step 5: Verify Report Structure

Validate that the report contains all required fields:

```bash
python code/eval/report_verifier.py
```

## Resource Monitoring

The pipeline includes built-in resource monitoring:

- **Memory Guard**: Automatically exits if RAM usage exceeds 6.5 GB
- **Timeout Guard**: Terminates execution after 6 hours
- **Batch Auto-Reducer**: Splits large batches if memory pressure is detected

To monitor resource usage in real-time, check the logs:
```bash
tail -f logs/execution.log
```

## Troubleshooting

### Out of Memory Errors

If you encounter memory errors:
1. Reduce context window size in `code/utils/config.py`
2. Reduce batch size to 1
3. Use streaming mode for large datasets (enabled by default)

### Dataset Download Failures

If the RULER dataset fails to download:
1. Check your internet connection
2. Verify HuggingFace is accessible
3. The system will fail loudly with a clear error message (no synthetic fallback)

### Long Execution Times

If execution exceeds 6 hours:
1. The Timeout Guard will automatically terminate the process
2. Consider running on a smaller subset of the RULER dataset
3. Use more CPU cores if available

## Output Files

After successful execution, you will find:

- `data/raw/ruler_dataset/`: Downloaded and verified RULER data
- `data/processed/`: Preprocessed data chunks
- `results/benchmark_report.json`: Final aggregated results
- `logs/execution.log`: Detailed execution logs with resource usage

## Verification

To ensure all components are working correctly:

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Verify report structure
python code/eval/report_verifier.py
```

## Notes

- **No GPU Required**: This pipeline is designed exclusively for CPU execution
- **No Quantization**: The MiniMax-M3 model runs in full precision (no 4-bit/8-bit quantization)
- **Real Data Only**: All results are computed from the real RULER dataset (no synthetic data)
- **Fail Loudly**: Any data fetch failure or memory constraint violation will cause an immediate exit with a clear error message