# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11 or higher.
- Git.
- **Materials Project API Key** (Optional but recommended for full data access). Set as environment variable `MP_API_KEY`.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-420-predicting-the-effect-of-alloying-on-the
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

The pipeline is executed via a single orchestration script.

1.  **Execute the main pipeline**:
    ```bash
    python code/main_pipeline.py
    ```

    This script will:
    - Check for `MP_API_KEY` and attempt data extraction from Materials Project/NIST.
    - Halt with a clear error if data is unavailable or N < 50.
    - Filter and clean the dataset (wt% -> at%, unit normalization).
    - Verify data independence (exclude derived Poisson's ratio).
    - Perform ILR transformation (SBP basis).
    - Train the Random Forest model with k-fold CV and an 80/20 split.
    - Compute Grouped ILR feature importance and VIF on ILR features.
    - Save results to `results/` with associational framing.

2.  **Verify outputs**:
    - Check `data/processed/alloys_clean.parquet` for the cleaned dataset.
    - Check `results/cv_metrics.json` and `results/test_metrics.json` for performance.
    - Check `results/feature_importance.json` for element rankings (Grouped ILR).
    - Check `results/vif_diagnostic.json` for collinearity flags (on ILR features).
    - Check `results/model_output.json` for the "Associational, Not Causal" disclaimer.

## Troubleshooting

- **Data Extraction Failure**: If the script halts with "Data Availability Failure" or "Insufficient Data", verify network access to Materials Project/NIST APIs and ensure `MP_API_KEY` is set if required. The project cannot proceed without valid data.
- **Memory Error**: Unlikely given the expected dataset size (<2000 rows). If encountered, check for infinite loops or accidental data duplication.
- **VIF Flag**: If `vif_flag` is True, review the ILR feature correlations. This is a diagnostic flag, not a failure (expected in some compositional subsets).
- **Model Performance**: If MAE > 0.05, check `results/test_metrics.json` for the "No Signal Detected" flag if the model performs no better than the null baseline.

## Output Interpretation

- **MAE**: Lower is better. An MAE > 0.05 is flagged as a potential model fit issue or high noise.
- **Feature Importance**: Higher scores indicate a stronger associational relationship with Poisson's ratio. Remember: **Correlation does not imply causation**. The scores are derived from Grouped ILR importance, not back-transformed splits.
- **VIF**: Values > 5 on ILR features indicate potential multicollinearity in the transformed space. This is a diagnostic flag.