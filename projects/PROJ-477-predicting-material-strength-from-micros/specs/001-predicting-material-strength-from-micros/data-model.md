# Data Model: Predicting Material Strength from Microstructure Images

## 1. Entity Definitions

### 1.1 MicrostructureImage
Represents a single 2D EBSD map.
*   **Attributes**:
    *   `image_id`: String (UUID or filename).
    *   `path`: String (relative path to image file).
    *   `width`: Integer (224).
    *   `height`: Integer (224).
    *   `channels`: Integer (3, normalized RGB or grayscale converted).
    *   `metadata_raw`: JSON (Original metadata from dataset).

### 1.2 GrainSizeFeature
Derived feature extracted from the image (FR-009). **Mandatory 1:1 relationship.**
*   **Attributes**:
    *   `image_id`: String (Foreign key to MicrostructureImage).
    *   `grain_size_mean`: Float (Average grain size in micrometers).
    *   `grain_boundary_count`: Integer.
    *   `extraction_method`: String (e.g., "OpenCV_Threshold").

### 1.3 YieldStrengthValue
The target variable associated with a microstructure image.
*   **Attributes**:
    *   `image_id`: String (Foreign key to MicrostructureImage).
    *   `value_mpa`: Float (Yield strength in MPa).
    *   `source`: String (e.g., "hall_petch_derived").
    *   `unit`: String ("MPa").

### 1.4 PredictionResult
Output of the model inference.
*   **Attributes**:
    *   `image_id`: String.
    *   `predicted_value`: Float.
    *   `confidence_lower`: Float (95% CI lower bound).
    *   `confidence_upper`: Float (95% CI upper bound).
    *   `error_mse`: Float (Squared error for this sample).
    *   `heatmap_path`: String (Path to Grad-CAM image).

### 1.5 ModelArtifact
The trained model state.
*   **Attributes**:
    *   `model_id`: String.
    *   `architecture`: String (e.g., "MobileNetV2").
    *   `epoch`: Integer.
    *   `val_loss`: Float.
    *   `weights_path`: String.
    *   `config`: JSON (Hyperparameters, seed).

## 2. Relationships

*   **MicrostructureImage** `1:1` **GrainSizeFeature**
    *   Every image has exactly one set of extracted grain features. **Mandatory.**
*   **MicrostructureImage** `1:1` **YieldStrengthValue**
    *   Every image has exactly one yield strength value (derived from grain size).
*   **MicrostructureImage** `1:1` **PredictionResult**
    *   Every image in the test set generates one prediction result.
*   **ModelArtifact** `1:N` **PredictionResult**
    *   One trained model generates predictions for the test set.

## 3. Data Flow

1.  **Ingestion**: Raw ZIP -> `data/raw/` (Checksummed).
2.  **Preprocessing**:
    *   Extract -> Validate (Image count).
    *   Resize (224x224) -> Normalize.
    *   Split -> `data/processed/train/`, `data/processed/val/`, `data/processed/test/`.
    *   Generate `manifest.json` (maps image filenames to IDs).
3.  **Feature Extraction (FR-009)**:
    *   Execute `code/data/extract_features.py` on all images.
    *   Output `grain_features.csv` (image_id, grain_size_mean).
4.  **Label Generation**:
    *   Join `manifest.json` with `grain_features.csv`.
    *   Compute `value_mpa` via Hall-Petch equation.
    *   Save `labels.csv`.
5.  **Training**:
    *   Read `manifest.json` + `labels.csv` -> `DataLoader`.
    *   Apply Augmentation -> Forward Pass -> Backward Pass.
    *   Save `ModelArtifact` to `results/artifacts/`.
6.  **Evaluation**:
    *   Load `ModelArtifact` -> `DataLoader` (Test, no augmentation).
    *   Compute MSE, R².
    *   **Execute `code/eval/interpret.py`**: Generate Grad-CAM and compute correlation with grain size. Output `results/interpretability_report.json`.
    *   **Execute `code/eval/sensitivity.py`**: Compute FPR/FNR using ground truth median. Output `results/sensitivity_report.json`.
    *   Save `results/metrics.json`.

## 4. Constraints

*   **Image Dimensions**: Fixed at 224x224.
*   **Value Range**: Yield strength > 0.
*   **Missing Data**: Images with missing strength values are excluded (max negligible tolerance).
*   **File Format**: Input images (JPG/PNG), Output heatmaps (PNG), Manifest/Labels (JSON/CSV).