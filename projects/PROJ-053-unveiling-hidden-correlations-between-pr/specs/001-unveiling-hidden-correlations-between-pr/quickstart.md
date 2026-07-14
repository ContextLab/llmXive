# Quickstart: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Prerequisites

- **Python**: 3.10 or higher
- **OS**: Linux (recommended for CI compatibility), macOS, or WSL2 on Windows.
- **Data**: A CSV file containing AM process parameters and mechanical properties.
  - *Note*: No verified public dataset is currently available. You must provide your own `data/raw/am_data.csv` or modify the download script to use a valid URL.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-053-unveiling-hidden-correlations-between-pr
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

### Option A: Using a Custom Dataset
1. Place your CSV file in `data/raw/am_data.csv`.
2. Ensure it has columns: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`.
3. (Optional) Include `alloy_type` for one-hot encoding.
4. (Optional) Create `data/baseline_importance.json` for SC-004 validation (see `contracts/` for schema).

### Option B: Automated Download (If a verified URL is found)
1. Update `code/data/download.py` with the verified URL.
2. Run the download script:
   ```bash
   python code/data/download.py
   ```
   *Note: Currently, this will fail gracefully with instructions for manual placement.*

## Running the Pipeline

Execute the full pipeline from preprocessing to visualization:

```bash
python code/main.py
```

### Expected Output
- **Logs**: `logs/preprocess.log`, `logs/training.log`
- **Data**: `data/processed/cleaned_data.csv`, `data/processed/normalization_bounds.json`
- **Models**: `models/gpr_model.pkl`, `models/baseline_model.pkl`
- **Results**: `results/metrics.json`
- **Figures**: `output/contour_yield_strength.png`, `output/uncertainty_heatmap.png`

## Verification

1. **Check Metrics**:
   Open `results/metrics.json` and verify `r2_score`, `rmse`, and `total_runtime_seconds` are present.
   ```json
   {
     "r2_score": 0.75,
     "rmse": 0.12,
     "total_runtime_seconds": 120.5,
     "n_samples": 150
   }
   ```

2. **Check Visualizations**:
   Open `output/contour_yield_strength.png`. Verify that:
   - The contour plot shows smooth transitions.
   - The uncertainty heatmap highlights regions with high variance (red zones).
   - Axis labels include physical units (e.g., "Laser Power (W)").

3. **Run Tests**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

- **Error: "Dataset missing required columns"**
  - Ensure your CSV has `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`.
- **Error: "Insufficient data for GPR training"**
  - Ensure your dataset has at least 50 rows.
- **Error: "No verified source found for AM-Machine-Learning"**
  - This is expected. Manually provide the dataset in `data/raw/am_data.csv`.
- **Warning: "High Uncertainty / Low Power"**
  - The synthetic data simulation indicated N=50 may be insufficient for robust non-linear detection. Interpret results with caution.

## Next Steps

- **Model Tuning**: Adjust `n_restarts_optimizer` in `code/models/gpr_trainer.py` for better hyperparameter search.
- **Feature Engineering**: Add derived features (e.g., `energy_density = laser_power / (scan_speed * layer_thickness)`) **ONLY** if you explicitly handle collinearity (not recommended for this pipeline).
- **Uncertainty Analysis**: Investigate regions with high uncertainty to design new experiments.