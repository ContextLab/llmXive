# Quickstart: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for dataset download)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-053-unveiling-hidden-correlations-between-pr
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

## Data Preparation

**Note**: The project requires a valid AM dataset. The implementation will attempt to download from the verified source **NIST AM-Bench** (Zenodo). If this dataset does not contain the required columns, the script will halt.

1.  **Run the data loader**:
    ```bash
    python code/main.py --step download
    ```
    *This step downloads the raw data, validates the schema, and saves it to `data/raw/`.*

2.  **Preprocess the data**:
    ```bash
    python code/main.py --step preprocess
    ```
    *This step performs median imputation, min-max normalization, and one-hot encoding. Output saved to `data/processed/`.*

## Training & Analysis

1.  **Train the GPR model**:
    ```bash
    python code/main.py --step train
    ```
    *Trains the model with 5-fold CV and saves the artifact to `results/model.pkl`.*

2.  **Generate results and plots**:
    ```bash
    python code/main.py --step analyze
    ```
    *Calculates metrics, performs permutation importance, and generates contour plots in `results/plots/`.*

## Expected Outputs

- `results/metrics.json`: Performance metrics (R², RMSE, MAE).
- `results/plots/contour_yield_strength.png`: Predicted yield strength map.
- `results/plots/uncertainty_heatmap.png`: Uncertainty distribution.
- `results/importance_ranking.json`: Ranked feature importance.

## Troubleshooting

- **"No verified open dataset found..."**: The pipeline cannot find the NIST AM-Bench dataset. Check `research.md` for the current dataset status.
- **"Insufficient data for GPR training..."**: The dataset has < 50 samples. A larger dataset is required.
- **"Zero variance detected..."**: A feature has identical values. It has been automatically removed.