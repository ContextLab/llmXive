# Quickstart: Mechanistic Interpretability of CTCF Binding-Site Selection

**Status**: BLOCKED. The pipeline cannot be executed.

## Prerequisites

- Python 3.11+
- Access to GitHub Actions (for execution) or a local CPU-only environment.
- Internet access to download from HuggingFace.
- **CRITICAL**: A verified source for multi-modal data (CTCF ChIP-seq, ATAC-seq, H3K27ac) must be identified before proceeding.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only versions to ensure compatibility with the free-tier runner.*

## Running the Pipeline

**WARNING**: The pipeline will fail at the data ingestion step due to missing verified sources.

### 1. Data Ingestion
Download the verified DNA dataset and prepare the windows.
```bash
python code/main.py --step ingest
```
*Output*: **BLOCKED**. No multi-modal dataset exists.

### 2. Model Training
Train the predictive model (CNN) on the sequence data.
```bash
python code/main.py --step train
```
*Output*: **BLOCKED**. No labels available.

### 3. Interpretability (SAE)
Train the Sparse Autoencoder and compute feature attributions.
```bash
python code/main.py --step interpret
```
*Output*: **BLOCKED**.

### 4. Validation
Run permutation tests to assess significance.
```bash
python code/main.py --step validate
```
*Output*: **BLOCKED**.

## Verification

- **Check**: The pipeline will not produce `data/metrics.json` or `data/significance_report.json`.
- **Action**: The project is currently blocked. The next step is to identify verified multi-modal ENCODE datasets or revise the project scope.

## Next Steps

1.  Search for verified ENCODE datasets containing CTCF ChIP-seq, ATAC-seq, and H3K27ac for at least 5 cell types.
2.  Update the `# Verified datasets` block with these sources.
3.  Re-run the planning phase.