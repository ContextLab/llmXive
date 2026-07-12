# Data Model: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

## Overview

This document defines the data structures, file formats, and schemas used throughout the research pipeline. All data is stored in `data/` with strict immutability for raw inputs and versioning for derived artifacts.

## Entity Definitions

### 1. StratifiedSubset
Represents a group of video sequences categorized by motion and texture.
- **Attributes**:
  - `subset_id`: String (e.g., "static_high")
  - `motion_level`: Enum {static, slow, fast}
  - `texture_level`: Enum {high, low}
  - `sequence_count`: Integer (Target: 50)
  - `sequence_ids`: List of String (Video IDs)
  - `source_path`: String (Path to extracted frames)

### 2. SparseFeatures
Represents extracted 2D coordinates and descriptors.
- **Attributes**:
  - `frame_id`: String
  - `video_id`: String
  - `keypoints`: Array of {x: float, y: float}
  - `descriptors`: Array of Float (SIFT/ORB vector)
  - `extraction_method`: Enum {SIFT, ORB}
  - `timestamp`: ISO8601

### 3. WarpingResult
Output of the latent warping and RBF interpolation.
- **Attributes**:
  - `frame_id`: String
  - `fundamental_matrix`: Array[3,3] Float
  - `inlier_count`: Integer
  - `reprojection_error`: Float
  - `occlusion_mask`: Binary Array (H, W)
  - `reconstructed_frame`: Path to image file
  - `status`: Enum {success, unsolvable, low_texture}

### 4. MetricReport
Aggregated results for statistical analysis.
- **Attributes**:
  - `video_id`: String
  - `subset_id`: String
  - `world_score`: Float (Dense baseline)
  - `sparse_consistency`: Float (Reprojection error)
  - `fid_score`: Float
  - `inference_time_sparse`: Float (seconds)
  - `inference_time_dense`: Float (seconds)
  - `peak_ram_sparse`: Float (MB)
  - `peak_ram_dense`: Float (MB)
  - `timestamp`: ISO8601

## File Formats

- **Raw Data**: `.tar.gz` (RealEstate10K)
- **Processed Frames**: `.png` (Lossless)
- **Features**: `.npy` (NumPy arrays for keypoints/descriptors)
- **Results**: `.json` (MetricReport), `.csv` (ANOVA tables)
- **Schemas**: `.schema.yaml` (YAML Schema for validation)

## Data Flow

1. **Ingest**: `data/raw/test.tar.gz` -> `data/processed/frames/`
2. **Stratify**: `data/processed/frames/` -> `data/stratified/{subset_id}/`
3. **Extract**: `data/stratified/{subset_id}/` -> `data/features/{subset_id}/`
4. **Compute**: `data/features/` -> `data/results/warping/`
5. **Evaluate**: `data/results/warping/` -> `data/results/metrics.json`
