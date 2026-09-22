# Quickstart: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Prerequisites
- Python 3.11+
- A verified AM dataset (CSV) with columns: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`.
  - *Note*: No verified source for "AM-Machine-Learning" exists in the provided list. You must provide a local file or a verified HuggingFace ID.
- **User-Provided Data Requirement**: If using a local file, you MUST also provide a `source_independence_log.txt` in `data/raw/` confirming the separation of process and property data streams.

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-053-unveiling-hidden-correlations-between-pr
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Place your dataset** in `data/raw/`.
    - Name it `am_raw_data.csv`.
    - Ensure it has the required columns.
    - Create `source_independence_log.txt` in the same directory.

## Running the Pipeline

### Step 1: Data Preprocessing
Run the preprocessing script to clean, normalize, and encode the data.
```bash
python code/preprocess.py --input data/raw/am_raw_data.csv --output data/processed/processed_data.csv
```
*Output*: `data/processed/processed_data.csv`, `results/preprocessing_log.txt`.

### Step 2: Model Training
Train the Gaussian Process Regression model and Linear Baseline.
```bash
python code/train_gpr.py --input data/processed/processed_data.csv --output results/metrics.json
```
*Output*: `code/models/gpr_model.joblib`, `results/metrics.json` (includes `runtime_seconds`, `baseline_r2`).

### Step 3: Visualization
Generate contour plots and uncertainty heatmaps.
```bash
python code/visualize.py --model code/models/gpr_model.joblib --data data/processed/processed_data.csv --output results/plots/
```
*Output*: PNG files in `results/plots/` (e.g., `yield_strength_contour.png`, `uncertainty_heatmap.png`).

### Step 4: Memory Profiling (Optional)
Run the memory profiling script to check resource usage.
```bash
python code/memory_profiling.py --input data/processed/processed_data.csv --output results/memory_profile.json
```
*Output*: `results/memory_profile.json` with memory usage metrics.

## Verification
- Check `results/metrics.json` for R² and RMSE values.
- Ensure `results/plots/` contains at least 3 PNG files (Contour, Uncertainty, Per Importance).
- Verify that `results/uncertainty_flags.json` exists and contains flagged regions.
- Verify that the pipeline ran without "Insufficient data" errors (N >= 50 required).
- Check `results/memory_profile.json` to ensure memory usage is within limits.
