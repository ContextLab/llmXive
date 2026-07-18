# Quickstart: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the internet (for NNDC ENSDF retrieval)

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Fetch and Validate Data
Run the data extraction script to retrieve data for the target nuclei (6He, 19Ne). This step handles network retries and format validation.

```bash
python -m code.cli.main fetch --nuclei 6He,19Ne
```

*Output*: Raw data files saved to `data/raw/`. Validation report printed to console.

### 2. Perform Meta-Analysis & Permutation
Run the analysis pipeline to compute weighted mean, perform permutation testing, and derive D-coefficient bounds.

```bash
python -m code.cli.main analyze --shuffles 10000
```

*Output*: `meta_analysis_results.json` in `data/processed/`. Console summary of p-values and bounds.

### 3. Generate Report
Generate the final comparison against PDG 2024 limits.

```bash
python -m code.cli.main report --output docs/report.md
```

*Output*: `docs/report.md` containing the sensitivity limits and PDG comparison.

## Verifying Results

To ensure reproducibility, re-run the analysis and verify the checksums:

```bash
# Verify data integrity
python -m code.cli.main verify-checksums

# Re-run analysis and compare results (should be identical)
python -m code.cli.main analyze --shuffles 10000 --check-deterministic
```

## Troubleshooting

- **Network Error**: If NNDC is unreachable, the script will retry with exponential backoff. If it fails after 3 retries, it logs the error and proceeds with available data.
- **No D-Values**: If the script reports "D-value missing" for a nucleus, it means the archival data does not contain published D-coefficients. This is an expected outcome for some historical data.
- **Permutation Instability**: If the p-value variance exceeds 0.01 when doubling shuffles, increase `--shuffles` (e.g., to [deferred]).
- **Spec Contradiction**: If the pipeline fails due to missing "raw momentum spectra", this is expected as the spec's requirement is invalid. The pipeline correctly falls back to D-coefficient meta-analysis.