# Quickstart: Statistical Power Analysis of Openly Available fMRI Datasets

## Prerequisites

- Python 3.11+
- GB RAM, 14 GB disk (GitHub Actions free-tier compatible)
- Internet access (for downloading OpenNeuro data)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

Create `config.yaml` in project root:

```yaml
datasets:
  - id: "ds000030"
    paradigms: ["motor"]
  - id: "ds000206"
    paradigms: ["working_memory"]
  - id: "ds000117"
    paradigms: ["emotional_face"]
  - id: "ds000247"
    paradigms: ["auditory_oddball"]
  - id: "ds001141"
    paradigms: ["visual_motion"]

simulation:
  sample_sizes: [10, 20, 40, 60]
  smoothing_kernels: [low, moderate]  # Temporal smoothing in time points (equivalent to 4mm/8mm)
  num_iterations: 50
  random_seed: 42
  effect_sizes: [, 0.2, 0.5, 0.8, 1.0]
  alpha_thresholds: [, 0.05, 0.10]

preprocessing:
  roi_extraction: "standard"  # Uses standard anatomical masks (CPU-tractable)
  temporal_smoothing: true
```

## Running the Pipeline

### Step 1: Download Data

```bash
python code/main.py --action download --config config.yaml
```

- Downloads raw BIDS data to `data/raw/`
- Validates checksums; skips corrupted files

### Step 2: Estimate Noise

```bash
python code/main.py --action estimate_noise --config config.yaml
```

- Estimates noise characteristics from real data
- Outputs noise profiles to `data/derived/noise_profiles/`

### Step 3: Generate Synthetic Data

```bash
python code/main.py --action generate_synthetic --config config.yaml
```

- Generates synthetic time-series with known ground-truth effect sizes
- Outputs to `data/derived/synthetic_data/`

### Step 4: Run Power Analysis

```bash
python code/main.py --action analyze --config config.yaml
```

- Executes split-half validation loop (multiple iterations per sample size, effect size, alpha)
- Generates power curves and logistic regression models
- Outputs to `data/aggregated/`

### Step 5: Generate Report

```bash
python code/main.py --action report --config config.yaml
```

- Creates figures and tables in `results/paper/`
- Includes power curves, effect size comparisons, and model diagnostics

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/test_end_to_end_pipeline.py -v
```

### Contract Tests

```bash
pytest tests/contract/ -v
```

## Troubleshooting

### ROI Extraction Fails

- Check logs in `data/logs/roi_extractor.log`
- Verify anatomical masks are compatible with the dataset

### Memory Overflow

- System automatically samples subjects to fit available RAM
- Check `data/logs/memory_monitor.log` for sampling actions

### GLM Convergence Failure

- Discarded iteration logged; if >20% failures, result flagged as "Unreliable"
- Check `data/aggregated/replication_results/failure_summary.csv`

## Output Interpretation

- **Power Curve**: X-axis = sample size; Y-axis = empirical replication rate (True Positive Rate)
- **Logistic Regression**: Coefficients indicate effect of sample size, kernel, SNR, and interaction terms on replication success
- **FDR Correction**: Applied across paradigms; adjusted p-values reported in model output
- **Alpha Sensitivity**: Separate curves for each alpha threshold (0.01, 0.05, 0.10)