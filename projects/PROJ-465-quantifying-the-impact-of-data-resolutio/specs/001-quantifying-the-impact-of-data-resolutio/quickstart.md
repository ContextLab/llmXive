# Quickstart Guide: Quantifying Data Resolution Impact on GW Parameter Estimation

## Overview

This project quantifies how downsampling and quantization of gravitational wave strain data affect parameter estimation accuracy.

## Prerequisites

- Python 3.9+
- pip
- GWOSC API access (optional for real data)

## Installation

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd PROJ-465-quantifying-the-impact-of-data-resolutio
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

### 1. Download Data (Optional)

```bash
python code/data/download.py
```

### 2. Transform Data

```bash
python code/data/transform.py
```

### 3. Run Inference

```bash
python code/inference/run_bilby.py
```

### 4. Calculate Metrics

```bash
python code/analysis/metrics.py
```

### 5. Aggregate Results

```bash
python code/analysis/aggregate.py
```

## Output Artifacts

- `results/posteriors/`: Posterior distribution files
- `results/metrics/`: Bias and divergence metrics
- `results/aggregation_report.json`: Summary of resolution thresholds
- `results/summary_table.csv`: Final summary table
- `results/figures/sampling_rate_vs_bias.png`: Visualization plot

## Validation

Run the quickstart validation script:

```bash
python code/validation/run_quickstart.py
```

This script ensures all artifacts are generated and checksummed.
