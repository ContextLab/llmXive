# Data Model: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

## Entities

### 1. MicrostructureImage
Represents a 2D grayscale image of a microstructure.

- **Image ID**: Unique identifier (string)
- **Resolution**: 256x256 pixels (fixed)
- **Data Type**: `uint8` or `float32` (grayscale)
- **Metadata**:
  - `void_density`: Float (0.0–1.0)
  - `inclusion_density`: Float (0.0–1.0)
  - `spatial_topology_hash`: String (SHA-256 of image data)

### 2. StiffnessTensor
Effective elastic stiffness tensor calculated via FFT-based homogenization.

- **Tensor ID**: Unique identifier (string, matches Image ID)
- **Components**: 2D matrix (e.g., 3x3 for 2D plane strain)
  - `C11`, `C12`, `C22`, `C66` (Voigt notation)
- **Bounds Check**:
  - `within_voigt_reuss_hill`: Boolean
- **Units**: GPa (or consistent unit system)

### 3. PredictionResult
Output of the CNN model for a given image.

- **Prediction ID**: Unique identifier (string)
- **Input Image ID**: Reference to `MicrostructureImage`
- **Predicted Tensor**: 2D matrix (same format as `StiffnessTensor`)
- **Error Metrics**:
  - `mae`: Float (Mean Absolute Error)
  - `mse`: Float (Mean Squared Error)
  - `r_squared`: Float
- **Flags**:
  - `is_outlier`: Boolean (MAE > 5%)
  - `is_ood_density`: Boolean (density outside training range)

### 4. TrainingRun
Metadata for a single training run.

- **Run ID**: Unique identifier (string)
- **Model Path**: Relative path to saved weights
- **Hyperparameters**:
  - `learning_rate`: Float
  - `batch_size`: Integer
  - `epochs`: Integer
  - `optimizer`: String
- **Metrics**:
  - `train_loss`: Float
  - `val_loss`: Float
  - `fold_index`: Integer (for CV)

## Data Flow

1. **Generation**: `generate_microstructures.py` → `MicrostructureImage` + `StiffnessTensor`
2. **Training**: `train.py` consumes images/tensors → outputs `TrainingRun` + `PredictionResult`
3. **Evaluation**: `evaluate.py` computes metrics → updates `PredictionResult` with flags

## Storage Schema

- **Raw Data**: `data/raw/images/` (PNG/NPY) + `data/raw/metadata.csv`
- **Processed Data**: `data/processed/batches/` (PyTorch DataLoader batches)
- **Models**: `code/models/` (`.pth` files)
- **Reports**: `data/reports/` (JSON/CSV for metrics)
