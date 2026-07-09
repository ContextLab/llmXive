# Data Model: Predicting Material Stiffness from Microstructure Images

## 1. Overview

This document defines the data structures used in the project, including the synthetic microstructure images, the calculated stiffness tensors, and the model outputs. All data is stored locally in the `data/` directory.

## 2. Data Entities

### 2.1 MicrostructureImage
Represents a single 2D grayscale image of a microstructure.

- **Type**: `numpy.ndarray` (float32)
- **Shape**: (128, 128)
- **Range**: [0.0, 1.0] (0 = void, 1 = inclusion, or grayscale values)
- **Metadata**:
  - `image_id`: Unique identifier (string, e.g., "img_00001")
  - `density`: Volume fraction of inclusions (float, 0.0 to 1.0)
  - `topology_metric`: A quantitative measure of spatial arrangement (e.g., clustering coefficient) used for stratification.
  - `seed`: Random seed used for generation (int)
  - `generation_timestamp`: ISO 8601 timestamp (string)

### 2.2 StiffnessTensor
Represents the effective elastic stiffness tensor calculated via FFT-based homogenization.

- **Type**: `numpy.ndarray` (float64)
- **Shape**: (6,) or (3, 3) depending on symmetry representation. For 2D plane strain, typically 3 components ($C_{11}, C_{12}, C_{22}$) or 4 ($C_{11}, C_{12}, C_{21}, C_{22}$). We use a flattened vector of 6 components for generality.
- **Units**: GPa (or consistent with base material properties)
- **Validation**: Must be within Voigt-Reuss-Hill bounds. **Note**: This is a plausibility check, not the training target. The training target is the specific numerical value from the FFT solver.

### 2.3 PredictionResult
Output of the CNN model for a single image.

- **Type**: `pandas.DataFrame` or `dict`
- **Fields**:
  - `image_id`: Link to source image
  - `predicted_stiffness`: Array of predicted tensor components
  - `ground_truth_stiffness`: Array of true tensor components (from FFT)
  - `mae`: Mean Absolute Error for this instance (float)
  - `mse`: Mean Squared Error for this instance (float)
  - `density_bin`: Categorical bin (e.g., "0-20%", "20-40%")
  - `is_outlier`: Boolean (True if MAE > 5%)

## 3. File Formats

### 3.1 Images
- **Format**: PNG or TIFF (lossless compression).
- **Directory**: `data/raw/images/`
- **Naming**: `<image_id>.png`

### 3.2 Metadata
- **Format**: CSV
- **File**: `data/processed/metadata.csv`
- **Columns**: `image_id`, `density`, `topology_metric`, `seed`, `stiffness_tensor` (JSON string or comma-separated values)

### 3.3 Model Artifacts
- **Format**: PyTorch `.pt` or `.pth`
- **File**: `data/models/cnn_surrogate_v1.pt`
- **Content**: Model weights, optimizer state, training config (epoch, loss, etc.)

## 4. Data Pipeline

1.  **Generation**: `generate_microstructures.py` creates images and calculates stiffness.
2.  **Storage**: Images saved to `data/raw/images/`; metadata saved to `data/processed/metadata.csv`.
3.  **Preprocessing**: Metadata is loaded, split into train/val/test sets (k-fold, stratified by density and topology).
4.  **Training**: `train.py` reads images and labels, trains model, saves weights.
5.  **Evaluation**: `evaluate.py` loads model, predicts, calculates metrics, saves results to `data/processed/predictions.csv`.

## 5. Data Hygiene & Reproducibility

- **Checksums**: All generated files (images, metadata) are checksummed (SHA-256) and recorded in `state/.../artifact_hashes`.
- **Random Seeds**: All random number generators (numpy, torch, scikit-image) are seeded with a fixed value defined in `code/utils/config.py`.
- **Versioning**: Every data transformation produces a new file with a timestamped suffix (e.g., `metadata_v1.csv`, `metadata_v2.csv`).
