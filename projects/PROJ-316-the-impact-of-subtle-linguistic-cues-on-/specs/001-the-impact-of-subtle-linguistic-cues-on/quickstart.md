# Quickstart: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   Access to the verified datasets (via HuggingFace CLI or direct download links).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin specific versions of `nltk`, `pandas`, `scikit-learn`, `statsmodels`, and `matplotlib` to ensure reproducibility.*

## Data Setup

1.  **Download Datasets**:
    Use the verified URLs from `research.md` to download the Parquet files into `data/raw/`.
    ```bash
    # Example for one dataset (replace with actual download command)
    wget "https://huggingface.co/datasets/Fsoft-AIC/RobotDesign1M/resolve/main/conversations/test-00000-of-00088.parquet" -O data/raw/aic_robotdesign.parquet
    ```
2.  **Verify Checksums**:
    Run the provided checksum script to ensure data integrity (Constitution Principle III).
    ```bash
    python src/checksum.py
    ```

## Running the Pipeline

1.  **Power Analysis (Prerequisite)**:
    Determine the required sample size for the annotation study.
    ```bash
    python src/main.py --step power_analysis --output data/results/power_analysis_results.yaml
    ```
    *This will generate `power_analysis_results.yaml` with the required N.*

2.  **Lexicon Validation (FR-010)**:
    (Manual Step) Annotate 50 turns and run validation script.
    ```bash
    python src/main.py --step validate_lexicon --input data/raw/annotated_50.csv --output data/results/lexicon_validation_results.yaml
    ```

3.  **Feature Extraction**:
    Extract linguistic features from the raw data.
    ```bash
    python src/main.py --step extract --input data/raw/aic_robotdesign.parquet --output data/processed/features.csv
    ```
    *This will generate `features.csv` with columns: `first_person_count`, `hedge_count`, `sentiment_score`, etc.*

4.  **Human Annotation**:
    (Manual Step) Annotate the required N conversations based on Phase -1 results. Store metadata in `data/raw/rater_metadata.json`.

5.  **Statistical Analysis**:
    Run correlations, regression, and power analysis.
    ```bash
    python src/main.py --step analyze --input data/processed/annotated_features.csv --output data/results/stats_results.csv
    ```
    *This will generate `stats_results.csv` with coefficients, p-values (raw and adjusted), and VIFs.*

6.  **Sensitivity Analysis**:
    Run the leave-one-out sweep.
    ```bash
    python src/main.py --step sensitivity --input data/processed/annotated_features.csv --output data/results/sensitivity_analysis.csv
    ```

7.  **Visualization**:
    Generate plots and the summary report.
    ```bash
    python src/main.py --step viz --input data/results/stats_results.csv --output data/results/plots/
    ```

## Verification

To verify the extraction logic (US-1):
1.  Run the unit tests:
    ```bash
    pytest tests/unit/test_lexicon.py -v
    ```
2.  Run the integration test on a small synthetic dataset:
    ```bash
    pytest tests/integration/test_pipeline.py -v
    ```
    *Note: Synthetic data is used ONLY for code verification, not for the main analysis.*

## Troubleshooting

*   **Missing Columns**: If the script raises a "Missing column: text_content" error, check the dataset metadata. If `authenticity_score` is missing, ensure the annotation protocol has been run.
*   **Convergence Failure**: If the regression model fails to converge, check for perfect multicollinearity (VIF > 5) or zero-variance predictors. The script will log the specific error.
*   **Memory Issues**: If running out of RAM, reduce the sample size using the `--sample-size` flag in `main.py`.
