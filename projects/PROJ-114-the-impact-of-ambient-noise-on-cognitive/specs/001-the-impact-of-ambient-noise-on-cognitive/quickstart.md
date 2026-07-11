# Quickstart: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM (for CI runner)

## Setup

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-114-the-impact-of-ambient-noise-on-cognitive
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Download datasets**:
 ```bash
 python -c "from datasets import load_dataset; load_dataset('jumplander/J6-CFI-HQ-20K', split='train').to_json('data/raw/cfi_train.jsonl')"
 ```

## Running the Pipeline

### Step 1: Generate Synthetic Data (for testing only)

*Generates synthetic acoustic logs (simulated) and loads real CFI data for pipeline validation.*

```bash
python code/main.py --generate-synthetic --n-participants 150 --output data/raw/synthetic_logs.jsonl
```

### Step 2: Ingest, Validate, and Calibrate

*Checks calibration flags, 1-minute bin gaps, and schema.*

```bash
python code/main.py --ingest --raw data/raw/synthetic_logs.jsonl --validate
```

### Step 3: Compute Metrics with CFI Validation

*Calculates CFI with correlation check between RT and Error.*

```bash
python code/main.py --compute-metrics --input data/processed/cleaned_data.csv
```

### Step 4: Fit Primary Model

*Fits LMM, runs LRT, and calculates FWER.*

```bash
python code/main.py --fit-model --input data/processed/metrics_data.csv
```

### Step 5: Run Sensitivity Analysis

*Threshold sweeps and robustness checks.*

```bash
python code/main.py --sensitivity --input data/processed/metrics_data.csv
```

### Step 6: Generate Report

*Auto-generates paper draft and updates state hashes.*

```bash
python code/main.py --report --output docs/paper_draft.md
```

## Verification

- **Check data integrity**:
 ```bash
 sha256sum data/raw/synthetic_logs.jsonl
 ```
- **Run unit tests**:
 ```bash
 pytest tests/unit/
 ```
- **Run integration tests**:
 ```bash
 pytest tests/integration/
 ```

## Troubleshooting

- **Model convergence failure**: Check for collinearity (VIF > 5) or insufficient data.
- **Memory error**: Reduce `--n-participants` or sample data.
- **Missing dependencies**: Re-run `pip install -r code/requirements.txt`.
- **Calibration Fail**: Ensure synthetic data includes `calibration_status` field.
- **CFI Redundancy**: Check logs for "High correlation between RT and Error" warning.
- **Dataset Structure Mismatch**: If J6-CFI-HQ-20K lacks required columns, pipeline will fail with a clear error. Fallback to synthetic data for code validation only.