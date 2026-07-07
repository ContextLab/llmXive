# Quickstart: Neural Mechanisms Underlying Adaptive Decision-Making

## Prerequisites

- Python 3.11+
- Git
- 8GB+ RAM (recommended for local dev; CI has substantial memory capacity.)
- CPU-only environment (No GPU required)
- `datalad` or `openneuro-py` (for dataset download)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd neural-mechanisms-adaptive-decision
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # venv\Scripts\activate # Windows
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Setup

The pipeline expects data in the `data/raw/` directory.

1. **Download Verified Datasets**:
 The pipeline uses **OpenNeuro ds000202**.
 - Use `openneuro-py` or `datalad` to download the dataset:
 ```bash
 openneuro download --dataset ds000202 --directory data/raw
 ```
 - Or manually download from `https://openneuro.org/datasets/ds000202`.

2. **Verify Checksums**:
 Ensure file integrity by comparing against the `data/checksums.txt` file (generated during data ingestion).
 ```bash
 python code/utils/io.py --verify-checksums
 ```

## Running the Pipeline

The pipeline is executed via `main.py`.

1. **Run Data Validation & Preprocessing**:
 ```bash
 python code/main.py --stage preprocessing
 ```
 *Output*: `data/processed/roi_data.parquet` (with checksums)

2. **Run Belief Updating Model**:
 ```bash
 python code/main.py --stage modeling
 ```
 *Output*: `data/models/params.parquet`

3. **Run Neural-Behavioral Correlation**:
 ```bash
 python code/main.py --stage analysis
 ```
 *Output*: `results/neural_signatures.parquet`

4. **Run Sensitivity Analysis**:
 ```bash
 python code/main.py --stage sensitivity
 ```
 *Output*: `results/sensitivity_report.json`

5. **Generate Tasks & Report**:
 ```bash
 python code/main.py --stage reporting
 ```
 *Output*: `tasks.md`, `paper/stats.json`

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Run specific contract tests:
```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **OOM (Out of Memory)**: If running locally, reduce the `--sample-size` flag. On CI, the pipeline automatically downsamples.
- **Model Convergence Failure**: Check `logs/model_convergence.log`. Participants failing times are excluded.
- **Missing Data**: If `roi_data.parquet` is missing, ensure the OpenNeuro dataset was downloaded correctly and contains the required beta-maps/logs.
- **Data Validation Failure**: Run `python code/preprocessing/data_validation.py` to check for missing variables in the dataset.