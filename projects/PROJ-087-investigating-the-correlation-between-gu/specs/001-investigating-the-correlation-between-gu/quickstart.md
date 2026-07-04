# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Prerequisites

- Python 3.11+
- `pip`
- Access to the verified dataset URLs (or the official American Gut Project if the verified URLs lack data, though the pipeline will halt if unverified).

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

The pipeline expects raw data in `data/raw/`.
1.  Download the OTU table and metadata from the verified sources (or the official AGP source if the verified ones are insufficient, though the pipeline will halt if the URL is unverified).
2.  Place files in `data/raw/`.
3.  Ensure the filenames match the configuration in `code/config.py` (default: `otu_counts.parquet`, `metadata.csv`).

## Running the Pipeline

Execute the main analysis script:
```bash
python code/main.py
```

This will:
1.  Download/Load data.
2.  Filter samples (antibiotic use, missing sleep).
3.  Calculate alpha-diversity.
4.  Perform correlations with BH correction.
5.  Perform confounder adjustment (Permutation-based Partial Correlation).
6.  Run sensitivity analysis.
7.  Generate plots in `results/`.

## Verification

Check the output:
- `results/correlation_results.csv`: Contains `r`, `p_value`, `p_adjusted`.
- `results/adjusted_correlation_results.csv`: Contains confounder-adjusted results.
- `results/sensitivity_analysis.csv`: Contains sensitivity sweep results.
- `results/scatter_shannon_sleep.png`: Scatter plot with regression.
- `results/boxplot_diversity_sleep_quartile.png`: Boxplot of diversity by sleep quartile.

Run tests:
```bash
pytest tests/
```
*Note: `tests/test_ingestion.py` includes a specific test for the proxy variable fallback logic.*