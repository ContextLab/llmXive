# Quickstart: Predicting Alloy Phase Diagrams from Compositional Data

## Prerequisites

*   Python 3.11+
*   `pip`
*   Materials Project API Key (set as `MP_API_KEY` environment variable)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    cd projects/PROJ-485-predicting-alloy-phase-diagrams-from-com/code/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Data Ingestion and Descriptor Generation
Run the script to fetch data from the Materials Project API and generate features.
```bash
python data_ingestion.py --systems "Cu-Al,Fe-C" --output ../data/processed/alloy_features.csv
```
*   This script handles API rate limiting (`FR-007`) and logs errors (`FR-008`) via `utils.py`.
*   Output: `alloy_features.csv` containing compositions and descriptors.

### 2. Model Training
Train the Random Forest model with LOSO cross-validation.
```bash
python model_training.py --input ../data/processed/alloy_features.csv --output ../data/results/
```
*   Output: `model.pkl`, `metrics.json` (MAE, R² per fold, error flags).

### 3. Visualization
Generate phase diagram plots for specific systems.
```bash
python visualization.py --model ../data/results/model.pkl --system "Cu-Al" --output ../data/results/plots/
```
*   Output: `Cu-Al_phase_diagram.png` and `visual_metrics.json`. Note: For Fe-C, only primary lines will be shown.

## Verification

*   **Test Data Ingestion**: Run with `--systems "Cu-Al"` and verify `alloy_features.csv` has >5 rows and correct columns.
*   **Test Training**: Verify `metrics.json` contains `mae`, `r2`, and `error_flags` keys.
*   **Test Visualization**: Verify `Cu-Al_phase_diagram.png` exists and contains two lines (experimental vs. predicted). Note: For Fe-C, only primary lines will be shown.