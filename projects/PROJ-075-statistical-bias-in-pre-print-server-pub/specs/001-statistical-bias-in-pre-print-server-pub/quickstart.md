# Quickstart: Statistical Bias in Pre-Print Server Publication Trends

## Prerequisites

-   Python 3.11+
-   `pip` and `venv`
-   Access to the internet (for fetching OpenAlex data and PDFs)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-075-statistical-bias-in-pre-print-server-pub
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `pandas`, `scipy`, `pdfplumber`, `requests`, `datasets`.*

## Data Setup

1.  **Download OpenAlex Metadata**:
    The script `code/01_fetch_and_match.py` is configured to fetch data from the verified Hugging Face source. Ensure you have sufficient disk space for the subset.

The research question, method, and references remain unchanged as they were not included in the provided text.
    ```bash
    python code/01_fetch_and_match.py --download-only
    ```
    *Output*: `data/raw/openalex_subset.parquet`

2.  **Verify Checksums**:
    The script automatically verifies the checksum of the downloaded data against the manifest in `state/.../artifact_hashes.yaml`.

## Running the Pipeline

To run the full pipeline (Fetch -> Match -> Extract -> Analyze):

```bash
python code/main.py
```

This will:
1.  Fetch and match pre-prints to journals.
2.  Download and parse PDFs for statistical metrics.
3.  Perform p-curve and effect-size analysis.
4.  Generate `data/processed/matched_pairs.csv` and `data/processed/analysis_results.json`.

### Running Specific Steps

-   **Only Match**:
    ```bash
    python code/01_fetch_and_match.py
    ```
-   **Only Extract Stats**:
    ```bash
    python code/02_extract_stats.py --input data/processed/raw_matches.parquet
    ```
-   **Only Analyze**:
    ```bash
    python code/03_analysis.py --input data/processed/matched_pairs.csv
    ```

## Output Interpretation

-   **`matched_pairs.csv`**: The clean dataset of matched pre-print/journal pairs with extracted metrics.
-   **`analysis_results.json`**: Contains:
    -   `p_curve_results`: Density ratio at p=0.05, estimated power.
    -   `effect_size_diff`: Mean $\Delta$ES, 95% CI, p-value from paired test.
    -   `sensitivity_analysis`: Flip rates at 0.01, 0.05, 0.1 thresholds.

## Troubleshooting

-   **PDF Parsing Errors**: If `pdfplumber` fails to extract text, the script logs the error and excludes the pair. Check `logs/extraction_errors.log`.
-   **Memory Errors**: If running out of RAM, reduce the batch size in `code/02_extract_stats.py` (parameter `--batch-size`).
-   **Match Rate Low**: If the match rate is < 60%, check the fuzzy matching threshold in `code/utils/matching.py`.
