# Quickstart: Mindfulness Components and Delivery Formats in ASD Social Skills

## Prerequisites

*   Python 3.11+
*   `pip` (package manager)
*   Access to the GitHub Actions runner (or local environment matching specs: CPU-only, 7 GB RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-008-psychology-research
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
    *Note: `requirements.txt` pins versions compatible with CPU-only execution (e.g., `torch` CPU wheel if needed, though not used here).*

## Running the Pipeline

### 1. Data Collection
Fetch raw data from ClinicalTrials.gov and OSF.
```bash
python code/data/collector.py --start-year 2015 --end-year 2024
```
*Output*: `data/raw/clinical_trials.json`, `data/raw/osf_studies.json`.

### 2. Data Cleaning & Extraction
Validate, tag, and clean the data.
```bash
python code/data/cleaner.py --input data/raw/ --output data/processed/
```
*Output*: `data/processed/clean_studies.csv`, `excluded_studies.log`.

### 3. Effect Size Calculation
Compute Hedges' *g* for all included studies.
```bash
python code/analysis/effect_sizes.py --input data/processed/clean_studies.csv --output data/processed/effect_sizes.csv
```

### 4. Meta-Analysis & Visualization
Run the meta-analysis and generate plots.
```bash
python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --plots-dir viz/
```
*Output*: `viz/forest_plot.png`, `viz/funnel_plot.png` (if N >= 10), `data/processed/results.json`.

## Verification

Run the test suite to ensure reproducibility and schema compliance.
```bash
pytest tests/
```
*Expected*: All tests pass, including contract validation against `contracts/*.schema.yaml`.

## Troubleshooting

*   **API Rate Limits**: The collector automatically implements exponential backoff. If the pipeline hangs, check network connectivity.
*   **Missing Variables**: If `clean_studies.csv` is empty, check `excluded_studies.log` for common exclusion reasons (e.g., age range, non-RCT).
*   **Small Sample Size**: If `N < 20`, the pipeline will automatically suppress subgroup analyses and Q-tests, logging a warning and performing descriptive or Bayesian analysis.