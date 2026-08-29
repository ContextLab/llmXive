# Quickstart Guide: Statistical Bias in Pre-Print Server Publication Trends

This guide provides instructions to set up the environment and run the full pipeline to reproduce the analysis of statistical bias between pre-print (arXiv/bioRxiv) and peer-reviewed journal versions of scientific papers.

## Prerequisites

- Python 3.9 or higher
- `pip` package manager
- Sufficient disk space (approx. 5-10 GB) for data processing and temporary files
- Internet connection (required to fetch OpenAlex data and PDFs)

## 1. Setup Environment

Navigate to the project root directory and install dependencies:

```bash
cd code
pip install -r requirements.txt
```

Ensure the following dependencies are installed:
- `pandas`, `scipy`, `numpy`, `requests`, `pdfplumber`, `datasets`, `regex`, `rapidfuzz`, `pytest`, `statsmodels`, `pypcurve`

## 2. Directory Structure

The project expects the following directory structure relative to the project root:

```
.
├── code/ # Source code
├── data/
│ ├── raw/ # Raw downloaded data and logs
│ ├── processed/ # Intermediate processed datasets
│ └── results/ # Final analysis outputs
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── state/ # Project state tracking
```

If these directories do not exist, create them:

```bash
mkdir -p data/raw data/processed data/results
mkdir -p tests/unit tests/integration
```

## 3. Running the Pipeline

The pipeline consists of three main stages: **Fetch & Match**, **Extract Stats**, and **Analysis**.

### Step 1: Fetch and Match Pre-prints to Journals

This step downloads metadata from arXiv, bioRxiv, and OpenAlex, matches pairs, and applies filtering logic.

```bash
cd code
python 01_fetch_and_match.py
```

**Outputs:**
- `data/processed/matched_pairs.csv`: The primary dataset of matched paper pairs.
- `data/raw/exclusion_log.csv`: Log of excluded pairs with reasons.
- `data/raw/acquisition_validation.log`: Metrics on query size and match rates.

*Note: This step may take time depending on network speed and the size of the OpenAlex dump.*

### Step 2: Extract Statistics from PDFs

This step downloads the full-text PDFs for the matched pairs and extracts p-values and effect sizes.

```bash
python 02_extract_stats.py
```

**Outputs:**
- Updates `data/processed/matched_pairs.csv` with extracted statistics columns (`p_value_preprint`, `effect_size_journal`, etc.).
- Generates `data/processed/stats_extraction_log.csv` for any extraction failures.

*Note: Ensure you have enough disk space for PDF downloads. The script handles PDF parsing robustly but may skip unsupported file types.*

### Step 3: Run Analysis

This step performs p-curve analysis, density ratio tests, and paired effect-size comparisons.

```bash
python 03_analysis.py
```

**Outputs:**
- `data/results/analysis_results.json`: Detailed statistical results (p-curve power, p-hacking estimates, density ratios).
- `data/results/null_distribution.json`: Permutation test results for validation.
- `data/results/sensitivity_report.md`: Report on bias stability across different significance thresholds.

## 4. Running Tests

To verify the implementation, run the test suite:

```bash
cd code
pytest../tests/ -v
```

Key test modules:
- `tests/unit/test_matching.py`: Fuzzy matching logic.
- `tests/unit/test_extraction.py`: PDF parsing and inequality handling.
- `tests/unit/test_analysis_pcurve.py`: P-curve power estimation.
- `tests/integration/test_pipeline_us1.py`: End-to-end pipeline check on a small subset.

## 5. Reproducing Results

To reproduce the exact results from a previous run:

1. Ensure the `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml` file exists and contains the correct artifact hashes.
2. Verify that `data/processed/matched_pairs.csv` matches the expected hash in the state file.
3. Re-run `03_analysis.py`. The outputs in `data/results/` should match the previously recorded values (within floating-point tolerance).

## Troubleshooting

- **OpenAlex Load Failure**: If `datasets.load_dataset("openalex")` fails, check your internet connection and ensure the `datasets` library is up to date. The script will fail loudly with a `RuntimeError` if the data source is unavailable.
- **PDF Extraction Errors**: If specific papers fail extraction, check `data/processed/stats_extraction_log.csv` for details. Ensure `pdfplumber` is installed correctly.
- **Memory Errors**: If the pipeline runs out of memory during the OpenAlex fetch, the script uses streaming (`streaming=True`). Ensure your system has at least 4GB of free RAM.

## License

This project is part of the llmXive automated science pipeline. Refer to the main repository for licensing details.