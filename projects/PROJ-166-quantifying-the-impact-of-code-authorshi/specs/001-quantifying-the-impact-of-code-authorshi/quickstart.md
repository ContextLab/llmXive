# Quickstart: Quantifying the Association Between Code Authorship Diversity and Software Security

## Prerequisites

- Python 3.11+
- Git (command line)
- `cloc` tool (installable via `sudo apt install cloc` or `brew install cloc`)
- Standard RAM allocation (GitHub Actions Free Tier)

The research question remains: [Research Question]
The method remains: [Method]
References: [References]
- **Note**: This pipeline uses `git clone --shallow-since=2015-01-01` for each repository.

## Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-166-quantifying-the-impact-of-code-authorshi
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

3.  **Prepare Data**:
    Ensure `data/raw/` is empty. The pipeline will download the NVD feed automatically.
    The pipeline will generate the target repository list via GitHub API using a fixed seed.

## Running the Pipeline

Execute the main orchestration script:

```bash
python code/main.py
```

This script performs the following steps:
1.  **Download**: Fetches ALL NVD/CVE JSON feeds (historical to present) from the official feed. **ABORTS** if the feed is unreachable. Merges and deduplicates by CVE ID.
2.  **Generate Target List**: Creates a reproducible list of repositories via GitHub API (fixed seed, specific query).
3.  **Extract**: Clones repositories (`--shallow-since=2015-01-01`), runs `git log` and `cloc`.
4.  **Merge**: Joins metrics with CVE counts.
5.  **Model**: Fits the GLM (with `log(kloc)` as predictor), calculates VIF, applies BH correction.
6.  **Robustness**: Runs lagged variable analysis, interaction terms, Shannon entropy, and non-linearity checks.

## Outputs

- `data/processed/repo_metrics.csv`: The primary analysis dataset.
- `data/processed/model_results.json`: Statistical results (coefficients, p-values, power analysis).
- `data/processed/robustness_results.json`: Lagged, interaction, entropy, and non-linearity analysis.

## Testing

Run the unit and integration tests:

```bash
pytest tests/
```

**Key Tests**:
- `test_dataset_construction`: Verifies that a seed repository collection produces non-null metrics.
- `test_cve_zero_handling`: Ensures repos with no CVEs have `cve_count=0`.
- `test_vif_calculation`: Confirms VIF is calculated and flags > 5.
- `test_nvd_abort`: Verifies pipeline aborts if NVD feed is unreachable.
- `test_lagged_analysis`: Verifies the lagged variable analysis runs without error.
