# Quickstart: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Prerequisites

*   Python 3.11+
*   Git
*   GitHub Actions runner (or local environment for testing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-258-the-effect-of-simulated-social-rejection
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

## Running the Pipeline

### Option A: Full Run (with Mock Data for CI)
Since no verified behavioral dataset is available in the provided list, run the pipeline with mock data to validate the logic and CPU feasibility.
**Note**: The mock data is configured to generate a **Between-Subjects** design only. The "modulation" hypothesis cannot be tested with this mock data.

```bash
python code/main.py --mode mock
```

### Option B: Run with Real Data (If available)
If you have a local dataset that matches the schema (Single-Cohort with both tasks):

1.  Place your CSV/TSV files in `data/raw/`.
2.  Run:
    ```bash
    python code/main.py --mode real --input data/raw/your_data.csv
    ```
    *Note: If the dataset is not a single-cohort (i.e., IDs do not match across tasks), the script will flag the design as "Between-Subjects" and drop the "modulation" claim. If required variables are missing, the script will exit with code 1.*

## Expected Outputs

*   `data/processed/analysis_results.json`: Contains F-values, p-values, FDR-corrected p-values, and `modulation_claim_valid` flag.
*   `data/processed/sensitivity_report.md`: Table of results across α = {0.01, 0.05, 0.1} including power estimates.
*   `output/report.md`: Final research report with "associational" limitations and explicit statements about design validity.

## Testing

Run the test suite to verify data validation and statistical logic:

```bash
pytest tests/ -v
```

## Troubleshooting

*   **Exit Code 1**: Indicates missing variables (e.g., `Reaction_Time` not found) or memory overflow. Check logs in `logs/ingest.log`.
*   **Low Power Warning**: If N < 30 per group, the report will flag this. No action needed; the analysis proceeds with confidence intervals.
*   **Modulation Claim Invalid**: If the design is Between-Subjects, the report will state that the "modulation" hypothesis is untestable.
