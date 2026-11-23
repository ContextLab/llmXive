# Quickstart: 001-garment-text-fidelity

## Prerequisites

- **Python**: 3.11+
- **Hardware**: 8-core CPU, 8 GB+ RAM (Recommended for smooth operation; 7 GB minimum).
- **Network**: Access to HuggingFace Hub.

## Installation

1. **Clone the repository** and navigate to the feature directory:
   ```bash
   git checkout 001-garment-text-fidelity
   cd projects/PROJ-829-llmxive-follow-up-extending-fashionchame
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Benchmark

### Step 1: Data Preparation (Streaming)
The pipeline automatically streams data from **DeepFashion2** (not Human3.6M). No manual download is required.
```bash
# This will trigger the feasibility filter and subset selection
python code/run_benchmark.py --mode prepare
```

### Step 2: Execute the Benchmark
Run the full pipeline on a representative clip subset.
```bash
python code/run_benchmark.py --mode benchmark --subset-size 500
```
*Note: This command will:*
- *Load FashionChameleon weights (INT8).*
- *Stream DeepFashion2 clips (replacing Human3.6M as per scientific necessity).*
- *Generate/verify prompts via VLM.*
- *Compute LPIPS/SSIM and Latency.*
- *Perform ANOVA and Sensitivity Analysis.*

### Step 3: Review Results
Output files are saved in `data/processed/`:
- `fidelity_scores.parquet`: Detailed metrics per clip.
- `anova_results.json`: Statistical significance of feature-class differences.
- `latency_log.csv`: Per-frame timing data.
- `benchmark_report.md`: Human-readable summary.

## Troubleshooting

- **OOM Error**: If you encounter `MemoryError`, the pipeline should automatically switch to a smaller batch size. If it fails, reduce `--batch-size` in `config/settings.yaml` to 20.
- **VLM Timeout**: If the VLM verification takes too long, ensure you have a stable internet connection. The default timeout is 30s per clip.
- **Missing FashionChameleon Weights**: Ensure the weights are placed in `code/models/fashionchameleon/` as per the `requirements.txt` instructions.

## Validation

To verify the installation:
```bash
pytest tests/unit/test_metrics.py -v
```
This ensures LPIPS and SSIM calculations are working correctly before the full benchmark runs.