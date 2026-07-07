# Quickstart: Molecular Topology and Reaction Selectivity

## Prerequisites

- Python 3.11+
- `git`
- Access to GitHub Actions (for CI) or local environment with 7GB+ RAM.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-083-investigating-the-relationship-between-m/code/
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `rdkit`, `pandas`, `scikit-learn`, `statsmodels`.*

## Running the Pipeline

### 1. Data Ingestion & Filtering
```bash
python ingestion.py --dataset-url "https://huggingface.co/datasets/pingzhili/uspto-50k/resolve/main/data/train-00000-of-00001.parquet"
```
*Output*: `data/processed/eas_filtered.csv`

### 2. Descriptor Calculation
```bash
python descriptors.py --input data/processed/eas_filtered.csv
```
*Output*: `data/processed/descriptors.parquet`

### 3. Modeling
```bash
python modeling.py --input data/processed/descriptors.parquet
```
*Output*: `data/models/results.json`, `data/reports/figures/`

## Verification

- **Check Descriptors**: Ensure `descriptors.parquet` contains rows for Benzene, Toluene, Nitrobenzene with correct Wiener indices.
- **Check Metrics**: Verify `results.json` contains R² > 0.05 or "Insufficient Variance" halt message.
- **Check Logs**: Ensure no "Critical Error: Insufficient Data" messages.

## Troubleshooting

- **Memory Error**: Reduce dataset size or use `--sample N` flag if available.
- **Descriptor Failure**: Check `calculation_status` in `descriptors.parquet`.
- **Target Variance**: If "Insufficient Variance" is logged, the dataset may contain only symmetric reactants (e.g., all benzene).