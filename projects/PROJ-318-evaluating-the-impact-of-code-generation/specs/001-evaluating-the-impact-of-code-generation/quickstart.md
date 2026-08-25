# Quickstart: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Prerequisites

-   Python 3.10+ installed.
-   Git installed.
-   Access to the internet (for downloading models and repositories).
-   A GitHub Actions runner or a local environment with at least 7 GB RAM.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-318-evaluating-the-impact-of-code-generation/code
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `transformers`, `torch`, `bitsandbytes`, `sentence-transformers`, `scipy`, `requests`, `docstring_parser`.*

## Execution

### Step 0: Initialize Repo List (One-Time)
Fetch a representative set of top repositories and save them to `data/repo_list.json`.
```bash
python extract.py --init-repo-list
```
*Output*: `data/repo_list.json` (Frozen list of 20 repos).

### Step 1: Extract Data
Run the extraction script for the frozen list of repositories.
```bash
python extract.py --max-methods 100
```
*Output*: `data/raw/` directory containing JSON files for each repo.

### Step 2: Reference Validation (Blocking Gate)
Run the Reference-Validator Agent to verify all citations and data sources.
```bash
python -m llmxive.reference_validator --input data/repo_list.json --output logs/validation_report.json
```
*Note*: If validation fails, the pipeline stops. Results are written to `logs/validation_report.json`.

### Step 3: Generate Docstrings
Run the generation script. This will load the model and process the extracted data.
```bash
python generate.py --temperature 0.2 --quantization 4bit
```
*Output*: `data/processed/` directory containing results with generated docstrings.
*Note*: This step is time-consuming. It will monitor RAM and time, but the sample size is fixed at 100/repo to ensure completion within 6 hours.

### Step 4: Analyze Results
Run the analysis script to compute scores and statistical tests.
```bash
python analyze.py
```
*Output*: `data/processed/global_results.json` containing the Wilcoxon test results and aggregated metrics.

## Validation

To verify the pipeline on a single repository (e.g., `requests`):
```bash
python extract.py --repo requests --max-methods 50
python generate.py --input data/raw/requests_methods.json --output data/processed/requests_results.json
python analyze.py --input data/processed/requests_results.json
```

## Troubleshooting

-   **Memory Error**: If you encounter OOM, ensure `bitsandbytes` is installed and 4-bit quantization is enabled. The script should auto-fallback to 8-bit or full precision if 4-bit fails on CPU.
-   **AST Parsing Error**: The script will skip files that fail to parse. Check `logs/extract.log` for details.
-   **Timeout**: The fixed sample size (100/repo) is designed to complete within 6 hours. If the job exceeds a significant duration threshold, check for system slowdowns.
-   **Validation Failure**: If the Reference-Validator Agent fails, check `logs/validation_report.json` for missing or mismatched citations.