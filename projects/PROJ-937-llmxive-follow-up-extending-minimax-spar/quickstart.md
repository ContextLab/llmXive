# llmXive: MiniMax Sparse Attention Extension - Quick Start

This guide provides instructions for running the MiniMax Sparse Attention evaluation pipeline on a **CPU-only** environment with **7 GB RAM** constraints.

## Prerequisites

- Python 3.11+
- 7 GB+ available RAM
- No GPU required (CPU-only execution enforced)

## Installation

1. **Clone and Navigate**:
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up-extending-minimax-spar
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

The project is organized as follows:
- `code/`: Source code for heuristics, evaluation, and utilities
- `data/raw/`: Raw RULER dataset (automatically downloaded on first run)
- `data/processed/`: Preprocessed data chunks
- `results/`: Final benchmark reports and statistical analysis
- `tests/`: Unit and integration tests

## Execution Workflow

The pipeline executes in three phases: Data Loading & Verification, Heuristic Execution, and Statistical Analysis.

### 1. Data Preparation (Automatic)

The first run of `code/main.py` will automatically download and verify the RULER dataset from HuggingFace.
- **Source**: `datasets.load_dataset("hkunlp/ruler")`
- **Verification**: SHA-256 checksum validation (Task T037)
- **Location**: `data/raw/ruler/`

### 2. Running the Main Pipeline

Execute the full evaluation on CPU:

```bash
python code/main.py --device cpu --heuristic block_entropy --subset small
```

**Arguments**:
- `--device`: Must be `cpu` (enforced by `utils/config.py`)
- `--heuristic`: Select heuristic (`block_entropy`, `gradient_magnitude`, `recency_bias`)
- `--subset`: Data subset size (`small`, `medium`, `full`)
- `--threshold`: Heuristic selection threshold (default: 0.05)

**Memory Safety**:
- The `MemoryGuard` (Task T040) monitors RAM usage.
- If usage exceeds **6.5 GB**, the process exits with code 1 to prevent OOM crashes.
- `code/data/preprocess.py` automatically reduces batch size if memory pressure is detected.

### 3. Running Baseline (Dense Attention)

To generate the ground truth baseline for comparison:

```bash
python code/eval/baseline_runner.py --device cpu --subset small
```

This produces `results/baseline_metrics.json` required for statistical comparison.

### 4. Statistical Analysis

After running heuristics and baseline, run the statistical aggregation:

```bash
python code/eval/report_generator.py
```

This generates `results/benchmark_report.json` containing:
- Exact Match & F1 scores
- Perplexity (PPL)
- Paired t-test p-values (Primary)
- Wilcoxon signed-rank test (Secondary)
- Sensitivity analysis tables
- False positive rates

## Unit Tests

Run the full test suite to verify implementation:

```bash
pytest tests/unit/ -v --cpu-only
```

**Key Test Files**:
- `tests/unit/test_heuristics.py`: Tests for entropy, gradient, and recency heuristics
- `tests/unit/test_metrics.py`: Tests for Exact Match, F1, and Perplexity
- `tests/unit/test_statistical.py`: Tests for t-test, Wilcoxon, and Holm-Bonferroni correction

## Troubleshooting

### Memory Errors
If you encounter `MemoryError` or the process exits with code 1:
1. Ensure no other heavy applications are running.
2. Reduce the `--subset` size (e.g., use `small` instead of `medium`).
3. Check `code/utils/resource_monitor.py` logs for memory usage history.

### Data Integrity Failures
If data verification fails:
1. Delete `data/raw/ruler/` directory.
2. Re-run `code/main.py` to trigger a fresh download and checksum verification.

### CUDA Errors
If CUDA errors appear:
1. Ensure `--device cpu` is explicitly passed.
2. Verify `utils/config.py` is enforcing CPU (`torch.set_device("cpu")`).
3. Check that `CUDA_VISIBLE_DEVICES` is unset or set to empty string.

## Output Artifacts

Upon successful completion, the following files are generated:
- `results/benchmark_report.json`: Final metrics and statistical significance
- `results/baseline_metrics.json`: Dense attention ground truth
- `results/sensitivity_analysis.json`: Threshold variance table
- `logs/execution.log`: Detailed resource usage and heuristic logs

## License

This project is part of the llmXive automated science pipeline.
See `LICENSE` for details.