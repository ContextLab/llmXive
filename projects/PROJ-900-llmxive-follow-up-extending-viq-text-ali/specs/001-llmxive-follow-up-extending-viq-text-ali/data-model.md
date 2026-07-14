# Data Model: llmXive follow-up: extending "ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

## 1. Overview

This document defines the data schemas, transformations, and storage formats for the ViQ resolution-invariance experiment. All data flows from `data/raw` (immutable) to `data/processed` (derived) and finally to `data/results` (metrics).

## 2. Data Entities

### 2.1 Raw Datasets (Immutable)

-   **COCO Train**: Parquet files containing `image` (bytes) and `caption` (string).
    -   *Source*: `yhshin1020/coco-img-caption-pairs`
-   **ImageNet-1K**: Tar archive or Parquet containing `image` (bytes) and `label` (int).
    -   *Source*: `vaishaal/ImageNetV2`

### 2.2 Processed Data (Derived)

-   **`processed_coco_64x64.parquet`**:
    -   Resized images to 64x64.
    -   Normalized pixel values (0-1).
    -   Columns: `id`, `image_64x64`, `caption`.
-   **`processed_imagenet_1024x1024.parquet`**:
    -   Sampled subset of ImageNet (N=100).
    -   Native resolution (1024x1024).
    -   Columns: `id`, `image_1024x1024`, `label`, `texture_complexity`.
-   **`processed_coco_eval_1024x1024.parquet`**:
    -   Sampled subset of COCO (N=100) for evaluation.
    -   Native resolution (1024x1024).
    -   Columns: `id`, `image_1024x1024`, `caption`, `texture_complexity`.

### 2.3 Results (Metrics)

-   **`results/training_metrics.json`**:
    -   Epoch-wise loss, codebook usage, convergence status.
-   **`results/inference_metrics.json`**:
    -   Per-image metrics: `id`, `psnr`, `ssim`, `cosine_similarity`, `texture_complexity`, `reconstruction_error`, `dataset_source`.
-   **`results/correlation_analysis.csv`**:
    -   Aggregated statistics: `metric`, `correlation_coefficient`, `p_value`, `sample_size`, `test_type`.

## 3. Data Flow

1.  **Ingestion**: Download raw data from verified URLs to `data/raw/`. Compute checksums.
2.  **Preprocessing (Training)**:
    -   Load COCO -> Resize to 64x64 -> Normalize -> Save to `data/processed/coco_64x64.parquet`.
3.  **Preprocessing (Evaluation)**:
    -   Load ImageNet/COCO -> Resize to 1024x1024 (if needed) -> Compute Texture Complexity (Laplacian) -> Save to `data/processed/eval_1024x1024.parquet`.
4.  **Model Execution**:
    -   Train on `coco_64x64` -> Save `codebook.pt`.
    -   Infer on `eval_1024x1024` -> Save `reconstructions/` (optional) and `inference_metrics.json`.
5.  **Analysis**:
    -   Load `inference_metrics.json` -> Compute Correlation -> Save `correlation_analysis.csv`.

## 4. Storage Constraints

-   **Raw Data**: Stored in `data/raw/` but not committed to Git (`.gitignore`). Downloaded on CI.
-   **Processed Data**: Compressed Parquet format to save space.
-   **Checkpoints**: `codebook.pt` (small, < 10MB).
-   **Images**: High-res reconstructions are NOT stored on disk to save space; metrics are computed on-the-fly or stored as small JSON.