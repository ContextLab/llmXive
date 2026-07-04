# Quickstart: Influence of Microstructural Features on Fatigue Life in Aluminum Alloys

## Prerequisites

-   Python 3.11+
-   Git
-   7 GB RAM available (free tier CI compatible)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-100-influence-of-microstructural-features-on
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `opencv-python`, `scikit-image`, `scikit-learn`, `pandas`, `numpy`.*

## Running the Pipeline

The pipeline is executed sequentially. Ensure you are in the project root.

### Step 1: Data Acquisition & Cleaning
Generates synthetic data (since verified domain data is unavailable) and cleans it.
```bash
python code/01_data_acquisition.py
```
*Output*: `data/processed/cleaned_specimens.csv`, `results/exclusion_report.log`.

### Step 2: Feature Extraction
Processes images (synthetic) and extracts features.
```bash
python code/02_feature_extraction.py
```
*Output*: `data/processed/feature_matrix.csv`.

### Step 3: Model Training
Trains RF, GB, ElasticNet with 5-fold Grouped CV.
```bash
python code/03_model_training.py
```
*Output*: `results/metrics.json`, `results/models/`.

### Step 4: Statistical Analysis
Runs ANOVA, bootstrapping, and sensitivity analysis.
```bash
python code/04_statistical_analysis.py
```
*Output*: `results/anova_summary.csv`, `results/sensitivity_report.json`.

### Step 5: Visualization
Generates plots.
```bash
python code/05_visualization.py
```
*Output*: `results/plots/*.png`.

## Verification

Check `results/metrics.json` for R², RMSE, and MAE.
Check `results/anova_summary.csv` for p-values and significance flags.
Ensure all plots are in `results/plots/` and <500KB.

**Note**: All results are derived from synthetic data and serve as a pipeline validation.