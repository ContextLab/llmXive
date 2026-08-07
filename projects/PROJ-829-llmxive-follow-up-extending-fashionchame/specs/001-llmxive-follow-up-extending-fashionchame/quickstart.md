# Quickstart: 001-garment-text-fidelity

## Prerequisites

*   Python 3.10+
*   Git
*   Access to Hugging Face (for DeepFashion2)
*   (Optional) Kaggle account for GPU offload (if CPU fails)

## 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

*Note: `requirements.txt` pins `transformers`, `scikit-image`, `scipy`, `pandas`, `datasets`, `opencv-python`, `mobileclip`.*

## 2. Data Preparation

The dataset is loaded via streaming. No manual download is required.

```bash
# Verify dataset access (optional)
python -c "from datasets import load_dataset; ds = load_dataset('zhengqin/DeepFashion2', split='train', streaming=True); print(next(iter(ds)))"
```

## 3. Running the Benchmark

Execute the full pipeline on a representative subset of the samples.

```bash
# Run the benchmark
python -m src.cli.main --subset-size 500 --batch-size 1 --output-dir data/reports
```

**Flags**:
*   `--subset-size`: Number of samples to process (default 500).
*   `--batch-size`: Frames per batch (default 1 for CPU safety).
*   `--output-dir`: Directory for results.

## 4. Verifying Results

Check the generated reports:

```bash
# View fidelity report
cat data/reports/fidelity_report.json

# View statistical analysis
cat data/reports/stats_report.json

# Check latency
cat data/reports/latency_report.json
```

**Expected Output**:
*   `fidelity_report.json`: Contains mean LPIPS/SSIM for `COLOR`, `PATTERN`, `TEXTURE`.
*   `stats_report.json`: Contains ANOVA p-value and Bonferroni correction status.
*   `latency_report.json`: Contains `pass` (True/False) based on 50ms threshold.

**Note**: Motion-based metrics (FR-006) are deferred and will not appear in the output.