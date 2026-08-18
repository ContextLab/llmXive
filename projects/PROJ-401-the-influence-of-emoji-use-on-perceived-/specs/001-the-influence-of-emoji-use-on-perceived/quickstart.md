# Quickstart: The Influence of Emoji Use on Perceived Emotional Intensity in Text

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local environment with 7GB+ RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-401-the-influence-of-emoji-use-on-perceived-/code
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

## Running the Pipeline

The pipeline is executed via `main.py`. It will automatically:
1.  Download the verified dataset (if available).
2.  Verify the presence of `human_intensity_score`.
3.  **If missing**: Generate a "Data Unavailable" report and exit.
4.  **If present**: Extract emoji features, run statistical analysis, and generate reports.

```bash
python main.py
```

### Expected Output

*   **Data Unavailable (Expected Outcome)**: `results/data_unavailable_report.md` detailing the missing `human_intensity_score` column.
*   **Success (Conditional)**: `results/analysis_report.json`, `results/correlation_plot.png`, `results/regression_coefficients.csv`, `results/reproducibility_report.md`, `results/performance_report.md`.

## Verification

To verify reproducibility:
1.  Run the pipeline twice.
2.  Compare the output checksums.
3.  Ensure `results/data_unavailable_report.md` (or `analysis_report.json`) matches exactly.

```bash
# Run twice and compare
python main.py
cp results/data_unavailable_report.md results/run1_report.md  # or analysis_report.json
python main.py
diff results/data_unavailable_report.md results/run1_report.md  # or analysis_report.json
# No output indicates success (files are identical)
```

## Troubleshooting

*   **Data Unavailable**: If the script halts with "Data Unavailable", this is the **expected outcome** given the current verified dataset list. The report details which fields were missing. No further action is required unless a new verified dataset with `human_intensity_score` is added to the project.
*   **Memory Error**: If loading the dataset fails, ensure `streaming=True` is used in the loader (implemented by default).
*   **Emoji Extraction Errors**: Ensure the `emoji` library is up to date.