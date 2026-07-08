# Quickstart: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Prerequisites

- Python 3.11+
- Git
- Access to the internet (for `gwpy` data fetch)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-465-quantifying-the-impact-of-data-resolutio
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

## Running the Pipeline

The pipeline is designed to run sequentially.

### Step 1: Fetch Data
Download high-SNR strain data from GWOSC.
```bash
python code/scripts/fetch_data.py --event GW150914
```

### Step 2: Preprocess
Downsample and quantize the data.
```bash
python code/scripts/preprocess.py --event GW150914 --rates 4096 2048 1024 --bits 32 16
```

### Step 3: Run Inference
Execute Bayesian parameter estimation.
```bash
python code/scripts/run_inference.py --event GW150914 --config all
```
*Note: This step may take 1-2 hours per configuration on a CPU.*

### Step 4: Analyze Metrics
Calculate Hellinger distances and bias.
```bash
python code/scripts/analyze_metrics.py --event GW150914
```

### Step 5: Aggregate Results
Generate the final summary report.
```bash
python code/scripts/aggregate_results.py
```

## Verification

To verify the pipeline on a single configuration:
```bash
python -m pytest code/tests/ -v
```

## Troubleshooting

- **GWOSC Timeout**: If `fetch_data.py` fails, check internet connectivity or GWOSC status.
- **Convergence Failure**: If `run_inference.py` flags "inconclusive", the `dlogz` threshold was not met within 5000 steps. This is expected for low-SNR or highly degenerate cases.