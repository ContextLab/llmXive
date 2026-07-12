# Quickstart: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## Prerequisites

-   Python 3.11 or higher.
-   Git.
-   Access to a machine with at least 8 GB RAM (recommended for smooth execution) or a GitHub Actions free-tier runner.
-   Internet connection (to download datasets and models).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc
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

## Running the Evaluation

The evaluation script runs the Gatekeeper and Baseline pipelines, computes metrics, and generates the report.

1.  **Download and Verify Dataset**:
    ```bash
    python code/cli/download_data.py
    ```
    *This script fetches the GateMem dataset from the verified HuggingFace URL, verifies the existence of all four required domains (medical, office, education, household), and saves them to `data/raw/`. If any domain is missing, the script exits with a clear error.*

2.  **Run the full benchmark**:
    ```bash
    python code/cli/run_evaluation.py --config config/default.yaml
    ```
    *This command executes the following:*
    -   Downloads and parses the dataset (with domain verification).
    -   Runs the Gatekeeper pipeline (DistilBERT + Rules).
    -   Runs the Baseline pipelines (Retrieval-only, Long-Context).
    -   Computes Access Control, **Utility (Conditional)**, **Overall Success Rate**, and Forgetting scores.
    -   Profiles CPU/RAM usage and calculates **Cost per Successful Task**.
    -   Performs statistical analysis (LMM with Episode ID random effect, or fallback **Wilcoxon**).
    -   Generates `data/processed/results_summary.json`.
    -   Extracts 50 failure cases to `data/samples/failure_cases.json`.

3.  **View the results**:
    -   Check `data/processed/results_summary.json` for the aggregated metrics.
    -   Review `data/samples/failure_cases.json` for manual error analysis.
    -   The console output will display the statistical significance of the differences.

## Troubleshooting

-   **Memory Error**: If you encounter `MemoryError`, ensure you are not running other heavy applications. The script attempts to process data in batches, but the LLM backbone may require significant RAM. Consider reducing the batch size in `config/default.yaml`.
-   **Model Download Failure**: If the DistilBERT model fails to download, the script will retry once. If it fails again, it exits with code 1. Check your internet connection and HuggingFace token permissions.
-   **Dataset Missing**: If the dataset cannot be found or a domain is missing, ensure the verified URL is accessible and the `data/raw/` directory exists. The script will explicitly state which domain is missing.

## Next Steps

-   **Manual Review**: Inspect the `data/samples/failure_cases.json` to understand the nature of False Positives and False Negatives.
-   **Paper Drafting**: Use the metrics from `results_summary.json` to draft the results section of the paper.
-   **Sensitivity Analysis**: Adjust the DistilBERT threshold or rule engine parameters to explore the trade-off curve between security and utility.