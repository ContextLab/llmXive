# Quickstart Guide: MiniMax Sparse Attention Evaluation (CPU-Only)

This guide provides step-by-step instructions to run the `llmXive` pipeline for evaluating MiniMax Sparse Attention heuristics on a CPU-only environment with 7 GB RAM constraints.

## Prerequisites

- **Hardware**: Multi-core CPU, 7 GB RAM (minimum), no GPU required.
- **Software**: Python 3.11+, pip.
- **Dependencies**: All required packages are listed in `requirements.txt`.

## 1. Project Setup

Ensure you are in the project root directory.

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

The pipeline enforces CPU-only execution and random seed pinning by default. You can override settings via environment variables or command-line arguments.

- **Memory Limit**: The system will automatically exit if RAM usage exceeds 6.5 GB (safety buffer).
- **Device**: Explicitly set to `cpu`.
- **Model**: Uses the frozen `MiniMax-M3` model (Index Branch disabled).

## 3. Data Download

The pipeline automatically downloads the RULER dataset from HuggingFace to `data/raw/` on the first run.

```bash
# Optional: Pre-download data to verify integrity
python code/data/ruler_loader.py
```

*Note: The loader includes checksum validation (T037) to ensure data integrity.*

## 4. Running the Pipeline

Execute the main entry point to run the full benchmark (Baseline + Heuristics + Statistical Analysis).

```bash
# Run the full evaluation on CPU
python code/main.py --device cpu
```

### Command-Line Arguments

- `--device`: Target device (default: `cpu`).
- `--heuristic`: Specific heuristic to run (`entropy`, `gradient`, `recency`). If omitted, all are run.
- `--threshold`: Sensitivity threshold for analysis (default: `0.05`).
- `--batch-size`: Batch size for inference (default: `1` to ensure memory safety).

## 5. Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **`results/benchmark_report.json`**: Contains F1 scores, perplexity, p-values (Paired t-test), and false-positive rates.
- **`data/processed/`**: Preprocessed dataset chunks.
- **Logs**: Structured JSON logs in `logs/` showing resource usage and exclusion counts.

## 6. Troubleshooting

### Out of Memory (OOM)
If the process exits with a memory error:
1. Verify no other heavy applications are running.
2. Ensure `--batch-size 1` is used.
3. Check `logs/` for the `ResourceMonitor` warning before exit.

### Missing "Needle" in Data
If samples lack the target string, the pipeline will log exclusion counts (Task T025) and skip those samples. Check `logs/exclusions.log` for details.

### Statistical Significance
The report includes both **Paired t-test** (Primary) and **Wilcoxon signed-rank test** (Secondary) results. A p-value < 0.05 indicates statistical significance.

## 7. Verification

To verify the installation and run unit tests:

```bash
pytest tests/unit/ -v
```

Ensure all tests pass before running the full benchmark.