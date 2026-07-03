# Quickstart: Evaluating Calibration of Predictive Intervals

## Prerequisites

*   Python 3.11+
*   Git
*   GitHub Actions Runner (or local machine with 2+ CPU cores, 7GB RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-721-evaluating-calibration-of-predictive-int
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Download M4 Dataset**:
    *   The script `code/data/download.py` will automatically fetch the dataset from the official M4 GitHub repository.
    *   It will verify the checksum against the expected value.
    *   *Note*: Ensure you have ~500MB of free disk space.

## Running the Pipeline

### Full Run (1,000 series)
```bash
python code/main.py --subset-size 1000 --seed 42
```
*   **Output**: Results in `results/` directory.
*   **Expected Runtime**: ~4-5 hours on 2 CPU cores.

### Quick Test (10 series)
```bash
python code/main.py --subset-size 10 --seed 42
```
*   **Purpose**: Verify pipeline correctness and coverage calculation.
*   **Expected Runtime**: < 10 minutes.

## Verifying Results

1.  **Check Coverage Rates**:
    *   Open `results/calibration_metrics.csv`.
    *   Verify `deviation_80` and `deviation_95` are within the expected range (≤2% for well-calibrated models).

2.  **Check Stratification**:
    *   Verify that `subgroup_seasonality` and `subgroup_trend` columns are populated correctly.

3.  **Check Recalibration**:
    *   If deviation > 2%, `results/recalibration_results.csv` should show improved coverage.

4.  **Run Contract Tests**:
    ```bash
    pytest tests/contract/
    ```
    *   Ensures all outputs conform to the defined schemas.

## Troubleshooting

*   **Memory Error**: Reduce `--subset-size` or increase swap space.
*   **Model Convergence Failure**: The pipeline logs warnings and skips the series. Check `logs/pipeline.log`.
*   **Missing Metadata**: If a series lacks `seasonality`, it is skipped. Check `logs/pipeline.log`.

## Next Steps

*   Review `research.md` for detailed methodology.
*   Analyze `results/` for insights into model calibration.
*   Extend the pipeline with additional models or datasets.
