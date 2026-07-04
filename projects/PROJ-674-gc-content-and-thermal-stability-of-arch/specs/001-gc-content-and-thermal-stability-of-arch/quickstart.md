# Quickstart: GC Content and Thermal Stability of Archaeal tRNA Stems

## Prerequisites

- Python 3.11+
- `git`
- Access to GitHub Actions (for CI) or local environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-674-gc-content-thermal-stability-of-arch
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
    *Dependencies include: pandas, numpy, scipy, biopython, statsmodels, requests, pyyaml, dendropy, scikit-learn.*

## Data Setup

The pipeline automatically downloads data on the first run, but you can manually trigger it:

```bash
python code/download.py
```
This script:
- Fetches OGT metadata from the verified BacDive URL.
- Downloads tRNA sequences from GtRNAdb.
- Performs fuzzy matching (Levenshtein > 0.9) to align species IDs.
- Validates the merged data against `contracts/dataset.schema.yaml`.
- Saves raw files to `data/raw/` and records checksums.

## Running the Analysis

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1.  Parse sequences and compute GC content (`code/parse.py`).
2.  Merge with OGT metadata.
3.  Perform WLS regression, LASSO, permutation tests (if tree available), and sensitivity analysis (`code/analyze.py`).
4.  Validate output against `contracts/analysis_output.schema.yaml`.
5.  Output results to `data/results/analysis_summary.json`.

## Verifying Results

Check the output file:
```bash
cat data/results/analysis_summary.json
```
Look for:
- `correlation_r`: The Pearson correlation coefficient.
- `permutation_p_value`: Significance from the null distribution (null if no tree).
- `caution_flag`: "Associational findings only..." if no phylogenetic tree was found.
- `m_des`: Minimum Detectable Effect Size.

## Testing

Run the test suite:
```bash
pytest tests/
```
- **Contract Tests**: Validate output against `contracts/` schemas.
- **Unit Tests**: Verify stem parsing logic and WLS weighting.

## Troubleshooting

- **Missing Data**: If fewer than 30 species are found, check the `data/processed/merged_dataset.csv` for missing OGT values or failed fuzzy matches.
- **Phylogenetic Tree Missing**: If no tree is found, the analysis will proceed with the associational flag. No error is raised.
- **Memory Errors**: The pipeline is designed for <7GB RAM. If errors occur, reduce the dataset size in `code/download.py`.
- **RNAfold Failure**: If `RNAfold` fails for a sequence, the script falls back to coordinate-based parsing or excludes the sequence (logged).