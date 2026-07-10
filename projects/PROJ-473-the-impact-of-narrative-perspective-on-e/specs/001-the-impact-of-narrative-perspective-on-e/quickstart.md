# Quickstart: The Impact of Narrative Perspective on Empathy and Moral Judgement

## Prerequisites
*   Python 3.11+
*   `git`
*   Access to a terminal with `pip` and `venv` support.
*   Access to the verified external datasets (OSF, Moral Foundations Twitter) as listed in `research.md`.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-473-the-impact-of-narrative-perspective-on-e
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This will install `spaCy` and the English model `en_core_web_sm`.*

4.  **Download the English language model**:
    ```bash
    python -m spacy download en_core_web_sm
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`. It performs the following steps in order:
1.  **Extraction**: Processes stories in `data/raw/stories/` to generate `data/processed/features.csv`.
2.  **Matching (Validation)**: Runs the similarity matching logic against the internal gold standard (real human data subset).
3.  **Data Loading**: Fetches the verified external reader-response dataset.
4.  **Analysis**: Runs the regression, VIF check, and sensitivity analysis.
5.  **Visualization**: Saves plots to `artifacts/`.

### Execute the Full Pipeline
```bash
python code/main.py --config code/config.py
```

### Run Specific Modules
*   **Feature Extraction Only**:
    ```bash
    python code/main.py --step extraction
    ```
*   **Statistical Analysis Only** (requires `data/processed/features.csv` and `data/processed/reader_responses.csv`):
    ```bash
    python code/main.py --step analysis
    ```

## Verifying Results

1.  **Check Logs**: Review `logs/pipeline.log` for warnings (e.g., "non-English text excluded", "VIF > 5.0").
2.  **Inspect Artifacts**:
    *   `artifacts/regression_plot.png`: Scatter plot with regression line.
    *   `artifacts/sensitivity_analysis.csv`: Results of the threshold sweep.
3.  **Validate Contracts**:
    ```bash
    python -m pytest tests/contract/
    ```
    This ensures the output schemas match the definitions in `contracts/`.

## Troubleshooting
*   **Memory Error**: Reduce the `MAX_STORIES` limit in `code/config.py`.
*   **Missing Model**: Ensure `en_core_web_sm` is downloaded (`python -m spacy download en_core_web_sm`).
*   **No Data**: Ensure `data/raw/stories/` contains at least one `.txt` file and that the external dataset is downloaded to `data/raw/`.