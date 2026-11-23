# Data Model: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Overview
This document defines the data structures used throughout the pipeline, ensuring consistency between data ingestion, model training, and evaluation. All data is stored in local directories with checksums for integrity.

## Key Entities

### MicrostructureImage
Represents a single micrograph.
- `file_path` (str): Absolute path to the image file.
- `alloy_family` (str): One of "steel", "al", "ti".
- `pixel_dimensions` (tuple): (width, height) in pixels.
- `intensity_array` (np.ndarray): 2D array of shape (128, 128), dtype float32, normalized [0, 1].
- `source_type` (str): "synthetic".

### FractureToughnessRecord
Links an image to a target value.
- `image_id` (str): Unique identifier for the image.
- `k_ic_value` (float): Fracture toughness in MPa·m^0.5 (synthetic ground truth).
- `alloy_family` (str): Inherited from the image.
- `split` (str): One of "train", "val", "test".

### ModelEvaluationResult
Represents the output of a model run.
- **Per-Run Output** (validates against `output.schema.yaml`):
    - `model_type` (str): "cnn", "linear", "random_forest".
    - `seed` (int): Random seed used.
    - `r_squared` (float): Coefficient of determination.
    - `mae` (float): Mean Absolute Error.
    - `rmse` (float): Root Mean Squared Error.
    - `run_time_seconds` (float): Execution time.
- **Aggregated Evaluation** (validates against `evaluation_schema.schema.yaml`):
    - `run_id` (str): Unique identifier for the run.
    - `model_type` (str).
    - `seed` (int).
    - `r_squared` (float).
    - `mae` (float).
    - `rmse` (float).
    - `alloy_family_metrics` (dict): Metrics broken down by alloy family.
    - `permutation_statistic` (float): Permutation test statistic (if applicable).
    - `permutation_p_value` (float): Permutation test p-value (if applicable).

### AttributionMap
Represents a Grad-CAM heatmap.
- `image_id` (str): ID of the source image.
- `heatmap_paths` (list of str): List of paths to generated heatmap images.
- `iou_scores` (list of float): IoU scores between augmented views.
- `mean_iou` (float): Average IoU score.
- `stability_threshold_met` (bool): Whether the mean IoU meets the stability threshold.

## Data Flow

1. **Raw Data Generation**: `code/data/synthetic_gen.py` generates raw images and a `metadata.csv`.
2. **Preprocessing**: `code/data/preprocess.py` converts to 128x128 grayscale, normalizes, and splits into `train/`, `val/`, `test/`.
3. **Feature Extraction**: `code/data/features.py` computes GLCM and power spectra for baselines.
4. **Training**: `code/models/train.py` produces `results.json` (per-run) and `evaluation_summary.json` (aggregated).
5. **Attribution**: `code/eval/attribution.py` produces `heatmaps/` and `stability_report.json`.

## Directory Structure

```text
data/
├── raw/
│   ├── images/          # Original images (128x128)
│   └── metadata.csv     # Image paths, alloy families, K_IC values
├── processed/
│   ├── train/
│   ├── val/
│   └── test/
├── explainability/
│   ├── heatmaps/        # Grad-CAM overlays
│   └── stability.json   # IoU scores
└── benchmarks/
    └── generator_runtime.json # Runtime metrics for data generation
```

## Checksums
- Every file in `data/raw` is checksummed (SHA-256) and recorded in `state/.../artifact_hashes`.
- No file in `data/` is modified in place; all transformations create new files.