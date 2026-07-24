# Quickstart: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Prerequisites

- Python 3.11+
- Git
- Docker (required for fMRIPrep)
- Access to OpenNeuro (or HuggingFace mirror if available)
- Sufficient disk space (for data download and processing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/neural-correlates-social-exclusion.git
    cd neural-correlates-social-exclusion
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

1.  **Download the dataset**:
    The pipeline attempts to download `ds000030` from OpenNeuro.
    ```bash
    python code/data_loader.py --dataset ds000030 --output data/raw
    ```
    *Note: If the dataset is not available in the verified HuggingFace mirrors, ensure you have network access to the OpenNeuro API. If no verified source is found, the pipeline will halt with `ERR_DATA_UNVERIFIED`.*

2.  **Verify data integrity**:
    ```bash
    python code/data_loader.py --verify
    ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1.  Download and verify data.
2.  Perform motion QC and exclude subjects (>3mm).
3.  Extract BOLD time-series from DMN ROIs.
4.  Compute connectivity strength for Inclusion and Exclusion.
5.  Run the paired permutation test.
6.  Generate figures and a summary report in `results/report.md`.

## Validation

To run unit tests:

```bash
pytest tests/
```

To validate data schemas:

```bash
python -m jsonschema validate data/processed/connectivity.parquet contracts/connectivity.schema.yaml
```

## Troubleshooting

- **ERR_N_INSUFFICIENT**: The dataset has fewer than 10 subjects after QC. The pipeline halts.
- **ERR_DATA_UNAVAILABLE**: The dataset could not be downloaded. Check network or verify the dataset ID.
- **ERR_DATA_UNVERIFIED**: No verified Cyberball dataset source was found in the project's verified dataset block. The study is blocked until a verified source is added.
- **Memory Error**: Ensure you are using the streaming mode in `data_loader.py` and not loading full NIfTI files into RAM.