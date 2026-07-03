# Quickstart: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-174-investigating-the-relationship-between-p
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

4.  **Verify Data Availability**:
    - **Crucial Step**: Run the verification script to ensure a valid eye-tracking dataset is available in the verified block.
      ```bash
      python code/verify_data_availability.py
      ```
    - **If this script exits with code 1**: The pipeline **cannot proceed** because no verified eye-tracking dataset was found. Do not attempt to run the main pipeline.
    - **If this script succeeds**: Proceed to the next step.

## Running the Pipeline

Execute the main orchestration script:

```bash
python code/main.py --config code/config.yaml
```

This will:
1.  Load and preprocess data (from verified source).
2.  Compute load proxies (with temporal alignment).
3.  Run correlations (with FDR correction and assumption checks).
4.  Fit LME models (with VIF checks and reduced model fallback).
5.  Train and evaluate the sliding-window classifier (with explicit ground truth labeling).
6.  Generate `results/` CSVs and `state/project_state.yaml`.

## Viewing Results

- **Correlations**: `results/correlations.csv`
- **Model Summary**: `results/model_summary.csv`
- **Classification**: `results/classification_metrics.csv`
- **Quality Report**: `results/quality_report.csv`

## Running Tests (Unit Only)

To run unit tests using synthetic data (does not affect empirical results):

```bash
pytest code/tests/ -v --test-mode
```

*Note: The `--test-mode` flag triggers synthetic data generation, which is hashed to `state/test_artifacts.yaml`.*

## Configuration

Edit `code/config.yaml` to adjust:
- Random seeds
- Filter cutoff frequency
- Classification thresholds
- Window sizes
- Temporal lag parameters

## Troubleshooting

- **Exit Code 1 on Verification**: No verified eye-tracking dataset found. Check the `# Verified datasets` block in the user message.
- **Memory Error**: Ensure you are using the verified dataset and that `data/processed/` is cleaned.
- **Missing Salience**: Check `results/quality_report.csv` for "target_salience missing" warnings. The model will automatically fit a reduced model.
- **VIF > 5**: The model will automatically drop the highest VIF predictor and log the change.
- **Circularity Warning**: If `results/classification_metrics.csv` contains "Search-Time Estimation (Self-Validated)", it means no independent ground truth was available.