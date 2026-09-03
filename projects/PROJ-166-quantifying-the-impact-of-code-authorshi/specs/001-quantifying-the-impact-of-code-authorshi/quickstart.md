# Quickstart: Quantifying the Impact of Code Authorship Diversity on Software Security

## Prerequisites

*   Python 3.11+
*   Git (command line)
*   `cloc` (Line of Code counter) installed on the system path.
*   14GB+ free disk space.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <project-repo-url>
    cd projects/PROJ-166-quantifying-the-impact-of-code-authorshi
    ```

2.  **Create Virtual Environment**:
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `cloc` is installed separately (e.g., `apt install cloc` or `brew install cloc`).*

## Running the Pipeline

Execute the main orchestration script:

```bash
python code/main.py
```

### What happens?
1.  **Ingestion**: Downloads the NVD CVE feed (or specific yearly files) and the list of target repositories.
2.  **Cloning**: Clones each repository with `--shallow-since=2015-01-01`.
3.  **Metric Calculation**: Runs `cloc` and `git log` to calculate `kloc` and `unique_authors`.
4.  **Matching**: Matches repositories to CVEs using substring URL matching.
5.  **Modeling**: Fits the Negative Binomial GLM (and ZINB/Ridge fallbacks) and performs robustness checks.
6.  **Correction**: Applies Benjamini-Hochberg correction to all p-values.
7.  **Output**: Generates `data/processed/model_results.json` and `data/processed/report.md`.

## Verifying Results

1.  **Check Data Integrity**:
    ```bash
    sha256sum data/nvd/*.json > data/nvd/checksums.txt
    # Verify against stored checksums
    ```
2.  **Inspect Output**:
    Open `data/processed/model_results.json` to view coefficients, standard errors, and adjusted p-values.
3.  **Validate Contracts**:
    The output JSON is validated against `contracts/output.schema.yaml` automatically during the run.

## Troubleshooting

*   **Disk Full**: The pipeline cleans up cloned repos after processing. If the run is interrupted, manually delete `data/repos/`.
*   **NVD Download Fail**: The script retries with exponential backoff. If it fails, check internet connectivity.
*   **`cloc` Not Found**: Ensure `cloc` is installed and in your `PATH`.
*   **Constitution Block**: If the pipeline aborts with "Constitution VI Amendment Required", ensure the Constitutional amendment to replace `--depth=1` with `--shallow-since` has been ratified in the repository.