# Quickstart: The Impact of Simulated Social Validation on Self-Perception in Adolescents

## Prerequisites

- Python 3.11 or higher
- `pip` (Python package installer)
- Git

## Installation

1.  **Clone the Repository** (if applicable) or navigate to the project directory.
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility (Constitution I).*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Data Generation & Validation
Run the data loader and validator. If real data is missing, it will automatically generate synthetic data.
```bash
python code/main.py --stage data
```
- **Output**: Validated dataset saved to `data/processed/validated_dataset.csv`.
- **Check**: Verify the log for "Data Gap: Switching to Synthetic Generation" if no real data was found.

### Step 2: Statistical Analysis
Run the regression model and robustness checks.
```bash
python code/main.py --stage analysis
```
- **Output**: Regression results (CSV/JSON) and VIF scores saved to `data/processed/results/`.
- **Check**: Ensure the output explicitly states "Associational" and lists VIF scores.

### Step 3: Visualization
Generate scatter plots and residual diagnostics.
```bash
python code/main.py --stage viz
```
- **Output**: PNG files saved to `data/processed/figures/` (e.g., `scatter_validation_vs_selfesteem.png`, `residuals.png`).

### Step 4: Full Run (End-to-End)
Execute all stages in sequence.
```bash
python code/main.py --stage full
```

## Verification

- **Reproducibility**: Re-run `python code/main.py --stage full` and verify that the output files (checksums) match the previous run (Constitution I).
- **Causal Language Check**: Inspect `data/processed/results/report.md`. It should contain no words like "causes", "leads to", or "determines".
- **Synthetic Ground Truth**: If using synthetic data, compare the estimated $\beta$ for `perceived_validation_score` against the known ground truth (default $\beta=0.3$) to verify model recovery.

## Troubleshooting

- **Error: "Data Gap"** (Expected if no real data): The system should automatically switch to synthetic generation. If it halts, check `code/data/validator.py` logic.
- **Error: "Memory Limit"**: If processing a large real dataset, ensure streaming is enabled or reduce the sample size in `code/data/generator.py`.
- **Error: "VIF > Threshold"**: Check `code/analysis/regression.py` for multicollinearity. Consider removing highly correlated predictors.
