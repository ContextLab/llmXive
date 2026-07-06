# Quickstart: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## Prerequisites

- Python 3.10+
- 7 GB+ RAM
- ~15 GB Disk Space (for raw data + intermediates)
- Internet access (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-498-investigating-the-relationship-between-n
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `mne`, `numpy`, `pandas`, `scipy`, `statsmodels`, `pytest`.*

## Data Setup

The pipeline automatically downloads the dataset on first run. If you need to manually verify or re-download:

```bash
python code/download_data.py --dataset ds004173 --output data/raw
```
*Note: The script will fetch ds004173 directly from OpenNeuro. If the dataset lacks 'switch'/'stay' labels, it will halt with an error.*

## Running the Pipeline

Execute the full analysis pipeline (Download → Preprocess → Synchrony → LMM):

```bash
python code/main.py
```

This will:
1.  Download and verify checksums.
2.  Preprocess EEG (filter, ICA, epoch) in batches.
3.  Compute phase differences (IPD) and wPLI.
4.  Fit LMM models with interaction terms (Synchrony * Condition).
5.  Save results to `data/processed/`.

## Verifying Results

Check the output logs and results:

```bash
# View the final statistical results
cat data/processed/lmm_results.csv

# Run contract tests to validate output schemas
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Ensure you are running on a machine with ≥7 GB RAM. The pipeline processes subjects sequentially and trials in batches; if it still fails, reduce the batch size in `code/main.py` (for testing only).
- **Dataset Not Found**: If `ds004173` is unavailable or lacks labels, check the logs for "Hypothesis Untestable". No alternative dataset will be used.
- **LMM Convergence Failures**: This is expected with small trial counts. The pipeline logs these warnings. Results with `convergence_status: failed` are excluded from final interpretation.
- **Circular Data**: Ensure the `sin_phase` and `cos_phase` columns are present in the synchrony features file; the LMM requires these for IPD.