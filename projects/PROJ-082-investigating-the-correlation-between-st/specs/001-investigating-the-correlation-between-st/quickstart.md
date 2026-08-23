# Quickstart: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Prerequisites

-   Python 3.11+
-   `pip` (package manager)

## Installation

1.  **Clone the repository** and navigate to the project root.
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

### Option A: With Real Data (if available)
1.  Place your `studies.csv` in `code/data/raw/`.
2.  Run the pipeline:
    ```bash
    python code/scripts/run_pipeline.py
    ```
3.  Check `code/data/processed/study_count.json` to see if the system entered "quantitative" or "narrative" mode.

### Option B: With Mock Data (For Testing)
If no real data is available, the pipeline can generate synthetic data to demonstrate functionality. **Note: This mock data is for CI testing only and does not answer the research question.**
```bash
python code/scripts/generate_mock_data.py --n-studies 15 --n-tracts 5 --output code/data/raw/studies.csv
python code/scripts/run_pipeline.py
```

## Expected Outputs

-   `code/data/derived/meta_result.json`: Statistical results (if N ≥ 10).
-   `code/data/derived/narrative_summary.json`: Text summary (if N < 10).
-   `code/data/derived/forest_plot.png`: Forest plot visualization.
-   `code/data/derived/funnel_plot.png`: Funnel plot visualization.
-   `code/data/processed/study_count.json`: Gate logic artifact (study count and tract count).

## Verification

To verify the statistical logic:
```bash
pytest code/tests/
```
This runs unit tests for the random-effects model, I² calculation, Egger's test, and **the N < 10 pivot logic**.