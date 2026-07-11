# Data Model: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Overview

This document defines the data structures used in the `code/` pipeline. All data flows from raw Parquet to processed latent vectors and finally to evaluation metrics.

## Entities

### 1. RawDocument

Represents a single row from the OmniDoc-1 dataset.

- `id`: Unique identifier (string)
- `image_bytes`: Binary image data (bytes)
- `annotations`: List of region annotations (see `RegionAnnotation`)
- `metadata`: Dictionary of additional metadata (e.g., source, page number)

### 2. RegionAnnotation

Represents a bounding box and modality label for a specific region.

- `bbox`: List of 4 floats `[x_min, y_min, x_max, y_max]`
- `modality`: Enum: `"text"`, `"image"`, `"mixed"`, `"unknown"`
- `confidence`: Float (0.0 to 1.0) - confidence of the modality label (if inferred)

### 3. LatentVector

Represents the encoded representation of a region.

- `id`: Unique identifier (string)
- `region_id`: Reference to `RegionAnnotation.id`
- `vector`: List of floats (dimension $D$, e.g., 256 or 512)
- `modality`: Enum: `"text"`, `"image"` (ground truth for evaluation)
- `source_image_id`: Reference to `RawDocument.id`

### 4. Centroid

Represents the mean vector of a cluster.

- `modality`: Enum: `"text"`, `"image"`, `"shuffled"` (for null control)
- `vector`: List of floats (same dimension as `LatentVector`)
- `count`: Integer (number of vectors averaged)
- `variance`: List of floats (variance per dimension)

### 5. EditedImage

Represents a generated image from vector arithmetic.

- `id`: Unique identifier (string)
- `source_latent_id`: Reference to `LatentVector.id`
- `operation`: String (e.g., "swap_text", "null_control")
- `decoded_image_bytes`: Binary image data (bytes)
- `metrics`: Dictionary of evaluation results (see `EvaluationMetrics`)

### 6. EvaluationMetrics

Stores the results of the analysis.

- `metric_name`: String (e.g., "accuracy", "ssim", "f1", "ocr_accuracy")
- `value`: Float
- `p_value`: Float (if applicable)
- `threshold`: Float (if applicable)
- `sample_size`: Integer

## Data Flow

1. **Ingestion**: `download_omnidoc.py` fetches `RawDocument` from Parquet.
2. **Preprocessing**: `preprocess_crops.py` extracts `RegionAnnotation` and crops images. **Excludes rows with `modality`="unknown" or "mixed".**
3. **Encoding**: `encode_latents.py` generates `LatentVector` for each crop.
4. **Analysis**:
   - `separability_test.py` computes `Centroid` and `EvaluationMetrics` (Accuracy, F1, p-value, triviality_flag, linearity_verified).
   - `editing_arithmetic.py` generates `EditedImage` and `EvaluationMetrics` (SSIM, OCR accuracy, null control comparison).
   - `robustness_checks.py` generates `EvaluationMetrics` for sensitivity sweep.
5. **Output**: All metrics are aggregated into a final JSON/Parquet report.

## Storage Format

- **Raw Data**: Parquet (compressed) in `data/raw/`.
- **Processed Data**: Parquet (compressed) in `data/processed/`.
- **Latents**: Parquet (compressed) in `data/latents/`.
- **Images**: PNG/JPEG in `data/images/`.
- **Metrics**: JSON in `data/metrics/`.