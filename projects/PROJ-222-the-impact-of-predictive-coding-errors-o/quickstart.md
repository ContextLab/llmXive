# Quickstart Guide: The Impact of Predictive Coding Errors on Subjective Time Perception

This guide outlines the steps to run the full analysis pipeline from data acquisition to visualization.

## Prerequisites

- Python 3.9+
- Virtual environment set up (see `code/requirements.txt`)
- Valid dataset IDs in `data/README.md` (see T050 for manual injection if blocked)

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Pipeline Execution

Run the full pipeline in sequence:

1. **Data Acquisition & Validation** (T012a-d, T043)
 ```bash
 python code/download.py
 python code/filter_datasets.py
 python code/update_readme.py
 python code/validate_manual_update.py
 ```

2. **Preprocessing** (T015, T016a-c, T041a-d)
 ```bash
 python code/preprocess.py
 python code/save_markov_artifacts.py
 ```

3. **Analysis** (T021a-d, T023a-c, T024-25, T026-28)
 ```bash
 python code/analysis.py
 ```

4. **Verification** (T017, T017b)
 ```bash
 python code/verify_standardized.py
 python code/run_t017b.py
 ```

5. **Visualization** (T030-32)
 ```bash
 python code/visualize.py
 ```

## Expected Outputs

- `data/processed/standardized.csv`: Standardized trial-level data
- `data/processed/markov_state.json`: Markov transition matrix
- `analysis/results.json`: Statistical analysis results
- `analysis/verification_log.json`: Verification logs for T017/T017b
- `figures/forest_plot.png`: Forest plot of effects
- `figures/residuals_*.png`: Residual diagnostic plots

## Troubleshooting

- **Blocked Status**: If `data/blocked_status.json` exists, manually add a verified dataset to `data/README.md` (T050) then run `python code/validate_manual_update.py`.
- **Missing Data**: Ensure `data/README.md` contains valid dataset IDs before running `download.py`.
- **Import Errors**: Verify virtual environment is active and all dependencies are installed.

## Reproducibility

To reproduce the analysis in a fresh environment:
1. Clone the repository
2. Follow the Installation steps
3. Ensure `data/README.md` contains valid dataset IDs
4. Run the Pipeline Execution steps in order
5. Verify outputs match expected files listed above