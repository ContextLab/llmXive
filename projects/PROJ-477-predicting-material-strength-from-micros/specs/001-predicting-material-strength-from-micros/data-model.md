# Data Model: Predicting Material Strength from Microstructure Images

## 1. Entity Definitions

### MicrostructureImage
Represents a 2D EBSD map of a polycrystalline material.
- **id**: Unique identifier (string, e.g., filename).
- **image_path**: Relative path to the 224x224 normalized image.
- **grain_size**: (Optional) Average grain size in micrometers (float).
- **orientation**: (Optional) Crystallographic orientation (string or vector).
- **source**: Original filename in raw dataset.

### YieldStrengthValue
The macroscopic mechanical property associated with a specific image.
- **value**: Yield strength in MPa (float).
- **unit**: "MPa" (string).
- **source**: Metadata file or derived label.

### PredictionResult
Output of the model for a specific image.
- **image_id**: Reference to MicrostructureImage.
- **predicted_strength**: Predicted yield strength (float).
- **ci_lower**: Lower bound of confidence interval (float).
- **ci_upper**: Upper bound of confidence interval (float).
- **grad_cam_path**: Path to the heatmap image.
- **actual_strength**: Ground truth yield strength (float).
- **error**: Squared error (float).

### BaselinePrediction
Output of the naive mean predictor for a specific image.
- **image_id**: Reference to MicrostructureImage.
- **baseline_strength**: Constant prediction (mean of training set).
- **baseline_squared_error**: Squared error of the baseline.

## 2. Data Flow

1. **Raw Input**: `data_synth_ebsd.zip` (Images + Manifest).
2. **Preprocessed**: `data/processed/` (224x224 PNGs + `manifest.csv`).
3. **Features**: `data/features/grain_features.csv` (Extracted grain metrics).
4. **Model Artifacts**: `models/checkpoint.pt` (Weights).
5. **Results**: `results/` (Metrics, predictions, heatmaps).

## 3. Schema Constraints

- **Image Dimensions**: Must be exactly 224x224 pixels.
- **Pixel Range**: Normalized to [0, 1] or [-1, 1] (float32).
- **Yield Strength**: Must be positive (>0).
- **Split Ratios**: Train/Val/Test split is deterministic (fixed seed).
- **Missing Data**: Any image without a matching strength value is excluded (error if >1%).