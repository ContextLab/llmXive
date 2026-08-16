# Quickstart: The Influence of Emoji Use on Perceived Emotional Intensity in Text

## Prerequisites
- Python 3.11+
- `pip` package manager

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `ml-datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `emoji`.*

## Running the Pipeline

The pipeline is designed to run end-to-end on a CPU.

1.  **Execute the main script**:
    ```bash
    python src/main.py
    ```
    This will:
    - Download/load the verified dataset.
    - **Validate** that the dataset contains human-rated intensity scores. **If missing, the script halts with an error.**
    - Extract emoji features.
    - Perform power analysis.
    - Run correlation and regression analyses.
    - Generate plots and save results to `data/processed/`.

2.  **Verify Outputs**:
    - Check `data/processed/analysis_ready.csv` for the combined features and human-rated scores.
    - Check `data/processed/results.csv` for statistical findings.
    - Check `output/` for visualization plots (e.g., `intensity_vs_emoji_count.png`).

## Testing

Run the test suite to ensure reproducibility and correctness:

```bash
pytest tests/ -v
```

- **Unit Tests**: Verify emoji extraction logic (FR-001).
- **Integration Tests**: Verify the full pipeline produces identical results on re-run (SC-004).
- **Data Validation Tests**: Verify that the pipeline halts if human-rated data is missing.

## Reproducibility Check

To verify reproducibility (Constitution Principle I):
1.  Run `python src/main.py` and save the output hash.
2.  Delete `data/processed/`.
3.  Run `python src/main.py` again.
4.  Verify that the new output hash matches the previous one.