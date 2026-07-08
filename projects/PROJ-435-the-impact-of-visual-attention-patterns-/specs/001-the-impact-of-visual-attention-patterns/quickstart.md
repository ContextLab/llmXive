# Quickstart: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Prerequisites
- Python 3.11+
- Git
- ~2 GB disk space (for synthetic data and dependencies)

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-435-the-impact-of-visual-attention-patterns-
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
    *Note: `requirements.txt` pins versions for `pandas`, `statsmodels`, `scikit-learn`, `datasets`, `pyyaml`.*

## Running the Pipeline

The pipeline is executed sequentially. Ensure you are in the project root.

### Step 1: Data Ingestion & Preprocessing
Generates synthetic data (or loads verified ROI data) and applies I-VT fixation detection.
```bash
python code/01_preprocessing.py
```
*Output: `data/processed/cleaned_fixations.csv`*

### Step 2: Valence Calculation
Calculates emotional valence for headlines using NRC/VADER.
```bash
python code/02_valence_calculation.py
```
*Output: `data/processed/valence_scores.csv`*

### Step 3: Data Merge
Merges gaze, valence, and participant data.
```bash
python code/03_data_merge.py
```
*Output: `data/processed/analysis_dataset.csv`*

### Step 4: Regression Analysis
Runs the mixed-effects model with the three-way interaction.
```bash
python code/04_regression_analysis.py
```
*Output: `output/regression_results.csv`*

### Step 5: Robustness Analysis
Runs sensitivity checks for fixation thresholds (50/100/150ms).
```bash
python code/05_robustness_analysis.py
```
*Output: `output/robustness_summary.csv`*

### Step 6: Visualization
Generates plots for the paper.
```bash
python code/06_visualization.py
```
*Output: `output/figures/`*

## Verification
To verify the pipeline:
1.  Check that `output/regression_results.csv` contains a column `p_value_interaction_3way`.
2.  Check that `output/robustness_summary.csv` contains rows for thresholds 50, 100, and 150.
3.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```

## Troubleshooting
- **Memory Error**: The pipeline is designed for ~7GB RAM. If running on a smaller machine, reduce the synthetic sample size in `01_preprocessing.py`.
- **Lexicon Error**: If NRC coverage is low, the script automatically switches to VADER and logs a warning.
