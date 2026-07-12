# Quickstart Guide: Molecular Complexity Analysis

This guide walks you through setting up the environment and running the molecular complexity analysis pipeline.

## Environment Setup

### 1. Python Version
Ensure you have Python 3.11 or higher installed:
```bash
python --version
```

### 2. Virtual Environment
Create a virtual environment to isolate dependencies:
```bash
python -m venv venv
```

Activate it:
- **Linux/macOS**: `source venv/bin/activate`
- **Windows**: `venv\Scripts\activate`

### 3. Install Dependencies
Install the required packages defined in `requirements.txt`:
```bash
pip install -r requirements.txt
```

> **Note**: This project requires `rdkit`, which may require system-level dependencies (e.g., `librdkit`) on some Linux distributions. If installation fails, refer to the RDKit installation guide for your OS.

## Running the Pipeline

The main entry point is `code/main.py`. It orchestrates the entire workflow:

```bash
python code/main.py
```

### What Happens When You Run It?

1. **Download & Sample**:
 - Connects to HuggingFace `sagawa/pubchemm-canonicalized`.
 - Loads the `canonical_smiles` and `cid` columns.
 - Applies stratified random sampling (default `SAMPLE_SIZE=5000` in `code/config.py`).
 - Saves the sample to `data/raw/pubchem_sample.csv`.

2. **Compute Metrics**:
 - Iterates through the sample in chunks (memory-safe).
 - Computes:
 - **Shannon Entropy**: Based on vertex degree distribution.
 - **LZ Complexity**: Based on SMILES string compression.
 - **Synthetic Accessibility (SA)** & **QED**: Using RDKit.
 - Handles timeouts and invalid molecules gracefully.
 - Saves results to `data/processed/metrics.csv`.

3. **Analysis**:
 - Calculates Pearson correlations between metrics.
 - Performs bootstrap resampling (1000 iterations) for confidence intervals.
 - Applies Bonferroni correction for multiple comparisons.
 - Saves results to `reports/stats.json`.

4. **Visualization**:
 - Generates scatter plots with regression lines for:
 - Entropy vs. SA
 - Entropy vs. QED
 - LZ vs. SA
 - LZ vs. QED
 - Saves plots to `reports/figures/`.

## Expected Outputs

After successful execution, check these directories:

- **`data/raw/pubchem_sample.csv`**: The sampled dataset.
- **`data/processed/metrics.csv`**: Computed metrics for each molecule.
- **`reports/stats.json`**: Statistical summary (correlations, p-values, CIs).
- **`reports/figures/`**: Four scatter plot PNG files.

## Troubleshooting

### Memory Errors
If you encounter memory issues, reduce `SAMPLE_SIZE` in `code/config.py` or ensure chunked processing is active.

### HuggingFace Connection Issues
Ensure you have internet access. The dataset is public, but large downloads may require a stable connection.

### RDKit Import Errors
If `ImportError: No module named 'rdkit'` occurs, verify the virtual environment is active and `requirements.txt` was installed correctly.

## Next Steps

- Review `reports/stats.json` to understand the correlations.
- Inspect `reports/figures/` for visual trends.
- Extend the analysis by adding new metrics in `code/metrics.py`.
- Run the test suite: `pytest tests/`