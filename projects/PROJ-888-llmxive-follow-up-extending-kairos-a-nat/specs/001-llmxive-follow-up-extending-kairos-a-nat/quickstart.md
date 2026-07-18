# Quickstart: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Prerequisites

-   Python 3.11+
-   7GB+ RAM available
-   14GB+ Disk space
-   Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/code/
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import torch; import datasets; import scipy; print('Dependencies OK')"
    ```

## Data Download

Run the download script to fetch the verified LIBERO dataset:
```bash
python download.py --source libero_hdf5
```
*Note: This will download the raw HDF5 file to `data/raw/`, verify the checksum, and perform schema compatibility checks.*

## Quantization Pipeline

Convert the raw data to discrete JSON vectors with sparsity simulation:
```bash
python quantize.py --bit-depth 4 --noise-std 0.1 --sparsity-stride 2 --sparsity-dropout 0.2 --output data/processed/quantized_4bit
python quantize.py --bit-depth 8 --noise-std 0.1 --sparsity-stride 2 --sparsity-dropout 0.2 --output data/processed/quantized_8bit
python quantize.py --bit-depth 12 --noise-std 0.1 --sparsity-stride 2 --sparsity-dropout 0.2 --output data/processed/quantized_12bit
python quantize.py --bit-depth 16 --noise-std 0.1 --sparsity-stride 2 --sparsity-dropout 0.2 --output data/processed/quantized_16bit
```

## Training & Evaluation

Run the full experiment sweep (4, 8, 12, 16-bit) with 10 independent runs:
```bash
python experiments.py --runs 10 --horizons 100,250,500 --sweep 4,8,12,16 --episodes 50
```

*This script will:*
1.  Load the Kairos model (with fallback to train-from-scratch if weights missing).
2.  Train on the CPU for each quantization level.
3.  Evaluate on horizons 100, 250, and 500 using **clean** ground truth.
4.  Log `ErrorMetric` to `data/results/mse_logs/`.
5.  Perform Levene's test, paired t-tests, and Wilcoxon tests.

## Statistical Analysis

View the aggregated results:
```bash
python stats.py --input data/results/mse_logs/
```
*Output: Summary table with MSE, p-values, and stability thresholds.*

## Validation

Check that all constraints are met:
```bash
python -m pytest tests/ -v
```
*Ensure no tests fail and RAM/CPU logs are within limits.*