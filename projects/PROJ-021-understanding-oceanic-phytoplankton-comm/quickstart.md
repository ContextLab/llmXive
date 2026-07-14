# Quickstart Guide: Understanding Oceanic Phytoplankton Communities

This guide provides step-by-step instructions to run the full pipeline for ingesting, preprocessing, training, and evaluating models on oceanic phytoplankton data.

## Prerequisites

- Python 3.11+
- Git
- At least 16GB RAM (recommended) and 50GB disk space
- Internet connection for data fetching

## Setup

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-021-understanding-oceanic-phytoplankton-comm
 ```

2. **Create a virtual environment and install dependencies**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

3. **Verify environment**:
 ```bash
 python -c "import torch; import xarray; import pandas; print('All dependencies installed successfully.')"
 ```

## Pipeline Execution

The full pipeline consists of four main stages: Data Fetching, Preprocessing, Model Training, and Evaluation. Run these scripts in order from the project root.

### 1. Fetch Data

Downloads raw satellite (MODIS) and reanalysis data to `data/raw/`.

```bash
python code/01_fetch_modis.py
```

*Note: Ensure you have sufficient disk space for the downloaded datasets.*

### 2. Preprocess Data

Aligns, coarsens, and masks the fetched data into a unified NetCDF artifact.

```bash
python code/02_preprocessing.py
```

**Outputs**:
- `data/processed/aligned_dataset.nc`: The unified dataset.
- `data/logs/interpolation_error.log`: Log of gap-filling errors.
- `data/logs/memory_enforcement.log`: Memory usage logs.

### 3. Train Models

Trains the Random Forest baseline and the lightweight VLM.

```bash
python code/03_model_training.py
```

**Outputs**:
- `data/artifacts/models/random_forest.pkl`: Trained RF model.
- `data/artifacts/models/vlm_model.pt`: Trained VLM model.
- `data/artifacts/training_metrics.json`: Training logs and metrics.

### 4. Evaluate and Visualize

Computes metrics, performs statistical tests, and generates spatial visualizations.

```bash
python code/04_evaluation.py
```

**Outputs**:
- `data/artifacts/model_comparison.csv`: Performance metrics for both models.
- `data/artifacts/basin_variance.json`: Variance metrics across ocean basins.
- `data/artifacts/basin_r2_difference.json`: R² difference between basins.
- `data/artifacts/feature_importance_maps/`: Directory containing spatial maps (PNG/GeoTIFF).
- `data/logs/importance_verification.log`: Verification of feature importance sums.

## Expected Artifacts

After running the full pipeline, verify the following files exist:

```text
data/
├── raw/
│ ├── reanalysis.nc
│ ├── modis.nc
│ └── seabass.csv
├── processed/
│ └── aligned_dataset.nc
└── artifacts/
 ├── models/
 │ ├── random_forest.pkl
 │ └── vlm_model.pt
 ├── model_comparison.csv
 ├── basin_variance.json
 ├── basin_r2_difference.json
 ├── training_metrics.json
 └── feature_importance_maps/
 └──... (visualization files)
```

## Troubleshooting

- **Memory Errors**: If you encounter `MemoryError`, reduce the `RAM_LIMIT_GB` in `code/utils/config.py` or sample the data more aggressively in `code/02_preprocessing.py`.
- **Data Fetch Failures**: Ensure your internet connection is stable and that the HuggingFace `datasets` library is up to date.
- **CUDA Errors**: This project is designed for CPU-only execution. If CUDA errors appear, ensure `torch` was installed with CPU support or set `CUDA_VISIBLE_DEVICES=""` before running.

## Next Steps

- Review `research.md` for analysis of the results.
- Check `data/logs/` for detailed pipeline execution logs.
- Explore `data/artifacts/feature_importance_maps/` for visual insights into driver contributions.