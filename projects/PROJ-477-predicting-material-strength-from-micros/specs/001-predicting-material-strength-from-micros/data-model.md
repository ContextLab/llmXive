# Data Model: Predicting Material Strength from Microstructure Images

## Overview

This document defines the data structures, schemas, and storage formats used throughout the project. It ensures consistency between data ingestion, model training, evaluation, and result reporting.

## Entities

### 1. Specimen

Represents a single material sample with a global mechanical property.
- **specimen_id**: Unique identifier (string).
- **yield_strength**: Measured or calculated yield strength in MPa (float, **required**).
- **grain_size_mean**: Average grain size of the specimen (float, optional).

### 2. MicrostructureImage

Represents a single 2D EBSD image and its associated metadata.
- **image_id**: Unique identifier (string, e.g., filename without extension).
- **specimen_id**: Reference to the parent specimen (string, **required**).
- **image_path**: Relative path to the image file.
- **width**: Original width in pixels (integer).
- **height**: Original height in pixels (integer).
- **grain_size**: Average grain size for this specific image (float, **required**). Extracted via OpenCV/Watershed.
- **orientation**: Crystallographic orientation data (string, optional).
- **yield_strength**: **Inherited** from the parent specimen (float, **required**).
- **split**: Data split assignment (`train`, `validation`, `test`).

*Note*: The `yield_strength` in `MicrostructureImage` is a denormalized copy of the value from the `Specimen` entity. All images sharing a `specimen_id` must have the same `yield_strength`.

### 3. PredictionResult

Represents the output of the model for a single image.
- **image_id**: Reference to the input image.
- **predicted_strength**: Predicted yield strength (float).
- **ci_lower**: Lower bound of the 95% confidence interval (float).
- **ci_upper**: Upper bound of the 95% confidence interval (float).
- **grad_cam_path**: Path to the generated heatmap image (string).
- **uncertainty_score**: Standard deviation of MC Dropout samples (float).

### 4. EvaluationMetrics

Aggregated metrics for the model performance.
- **model_name**: Name of the architecture (e.g., `MobileNetV2`).
- **mse**: Mean Squared Error on the test set (float).
- **r2**: Coefficient of Determination on the test set (float).
- **baseline_mse**: MSE of the naive mean predictor (float).
- **t_statistic**: t-statistic from the paired t-test (float).
- **p_value**: p-value from the paired t-test (float).
- **null_hypothesis_status**: `rejected` or `accepted` (string).
- **r2_threshold**: Threshold for null result (0.5).

## Storage Format

### Raw Data
- **Format**: ZIP archive.
- **Contents**: `images/` directory and `manifest.csv`.
- **Location**: `data/raw/`

### Processed Data
- **Format**: CSV (manifest) + PNG/JPG (images).
- **Location**: `data/processed/`
- **Structure**:
  ```text
  data/processed/
  ├── train/
  ├── validation/
  └── test/
  ```

### Results
- **Format**: JSON and CSV.
- **Location**: `results/`

## Data Flow

1.  **Ingestion**: Synthetic data generated to `data/raw/`. Checksum verified.
2.  **Preprocessing**: Images resized to 224×224, normalized, and split **by specimen**. Manifest updated with `specimen_id`.
3.  **Feature Extraction**: Grain size extracted and added to manifest.
4.  **Training**: Data loaded via `DataLoader` from `data/processed/`.
5.  **Evaluation**: Predictions saved to `results/predictions.csv`. Metrics saved to `results/metrics.json`.
6.  **Interpretability**: Heatmaps saved to `results/heatmaps/`.